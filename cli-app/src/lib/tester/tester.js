import fs from "fs";
import path from "path";
import { Worker } from "worker_threads";
import * as rax from 'retry-axios';
import axios from "axios";
import {HTTP_METHOD, PAYLOAD_TYPES, COLORS, TARGET_ENDPOINT} from "../../utils/constants.js";
import {PrintToConsole, SliceArrayIntoChunks} from "../../utils/utility.js";
const interceptorId = rax.attach();

export async function GeneratePayloadFromDirectory(directory, position, method, type) {
  let generatedPayloadObjects = await readFilesInDirectory(
    directory,
    position,
    method,
    type
  );
  return generatedPayloadObjects;
}

export async function orchestrateAttack(attackType, payloads, numberOfThreads) {
  let results = await SendPayloads(payloads, numberOfThreads);
  let resultsStore = {
    'type': attackType,
    'data': {}
  };
  for (let i = 0; i < results.length; i++) {
    let result = results[i];
    if (result.resp_status in resultsStore.data) {
      resultsStore.data[result.resp_status].push(result.payload);
    } else {
      resultsStore.data[result.resp_status] = [result.payload];
    }
  }
  resultsStore['total'] = payloads.length;
  return resultsStore;
}

async function SendPayloads(payloads, numberOfThreads) {
  let results = [];
  let workers = [];
  let numWorkers = Math.min(numberOfThreads, payloads.length);
  let completedWorkers = 0;
  let chunks = SliceArrayIntoChunks(payloads, numWorkers);
  // Function to handle worker completion
  const handleWorkerCompletion = async () => {
    completedWorkers++;
  };
  for (let i = 0; i < numWorkers; i++) {
    // Send data to the worker
    const worker = new Worker(import.meta.dirname + "/tester_worker.js");
    worker.postMessage({ formattedPayloads: chunks[i] });

    // Receive data from the worker
    worker.on("message", (result) => {
      results = results.concat(result);
    });
    worker.on("exit", handleWorkerCompletion);
    // Handle errors
    worker.on("error", (err) => {
      completedWorkers++;
      PrintToConsole(`Error in worker when sending traffic to testing enviornment: ${err.message}\n${err.stack}`,COLORS.RED);
      PrintToConsole(`This likely the case of the docker container unable to run properly. Common issues such as duplicate modsecurity rule id, malformat modsecurity rule, etc.`,COLORS.RED);
      PrintToConsole(`Will proceed to exit: ${err.message}\n${err.stack}`,COLORS.RED);
      process.exit(1);
    });
    workers.push(worker);
  }

  // Wait for all workers to complete
  await new Promise((resolve) => {
    const checkCompletion = () => {
      if (completedWorkers >= numWorkers) {
        resolve();
      } else {
        setTimeout(checkCompletion, 1000);
      }
    };
    checkCompletion();
  });
  return results;
}

// Review the need for payload.message
export async function SendPayload(formattedPayload) {
  let resp = null;
  try {
    if (formattedPayload.method == HTTP_METHOD.GET) {
      resp = await axios.get(formattedPayload.endpoint, getAxiosConfiguration(formattedPayload));
      formattedPayload.resp_status = resp.status;
    } else if (formattedPayload.method == HTTP_METHOD.POST) {
      // defaults to url form
      resp = await axios.post(
        formattedPayload.endpoint,
        formattedPayload.data,
        getAxiosConfiguration(formattedPayload)
      );
      formattedPayload.resp_status = resp.status;
    } else {
      formattedPayload.message = "error";
    }
  } catch (err) {
    if ("status" in err) {
      formattedPayload.resp_status = err.response.status;
    } else {
      formattedPayload.error = err;
      formattedPayload.message = "error";
    }
  } finally {
    if (formattedPayload.type == PAYLOAD_TYPES.PAYLOAD && formattedPayload.resp_status == 403) {
      // for payload, it should return status 403
      formattedPayload.message = "success";
    } else if (formattedPayload.type != PAYLOAD_TYPES.PAYLOAD && formattedPayload.resp_status == 200){
      // for simulated business traffic, it should return status 200
      formattedPayload.message = "success";
    } else {
      // if there are any other status code, it is an error
      formattedPayload.message = "error";
    }
  }
  return formattedPayload;
}

/**
 * Formats the raw payload string into a payload object
 * @param {string} position - where the payload should be
 * @param {string} method - type of http request
 * @param {string} payload - Actual payload
 * @param {string} type - refers is this is a business traffic or actual payload test
 * @returns {Object} - a formatted javascript object
 */
export async function FormatPayload(position, method, payload, type) {
  let target_endpoint = TARGET_ENDPOINT;
  let formatted_payload = {
    endpoint: target_endpoint,
    position: position,
    payload: payload,
    method: method,
    type: type,
  };
  if (method == HTTP_METHOD.GET) {
    // URL Parameter
    // ?payload={payload}
    formatted_payload.data = {
      payload: payload,
    };
  } else if (method == HTTP_METHOD.POST) {
    // Form URL Encoded
    // payload={payload}
    formatted_payload.data = {
      payload: payload,
    };
  } else {
    // Defaults to GET behavior
    formatted_payload.data = {
      params: {
        payload: payload,
      },
    };
  }
  return formatted_payload;
}

async function formatPayloads(payloads, position, method, type) {
  let formatted_payloads = [];
  for (let y = 0; y < payloads.length; y++) {
    let payload = payloads[y];
    if (payload.length > 0) {
      let formatted_payload = await FormatPayload(position, method, payload, type);
      formatted_payloads.push(formatted_payload);
    }
  }
  return formatted_payloads;
}

// Function to read all files in a directory
export async function readFilesInDirectory(directory, position, method, type) {
  let formatted_payloads = new Set();

  let directoryPath = directory;

  // Check if the path is absolute
  if (path.isAbsolute(directory)) {
    directoryPath = directory;
  } else {
    // If the path is relative, resolve it to an absolute path
    const baseDir = process.cwd();
    directoryPath = path.resolve(baseDir, directory);
  }

  try {
    const files = await fs.promises.readdir(directoryPath);
    for (const file of files) {
      const filePath = `${directoryPath}/${file}`;
      // Check if it is a file
      const stats = await fs.promises.stat(filePath);
      if (stats.isFile()) {
        let temp_results = await readFileLineByLine(
          filePath,
          position,
          method,
          type
        );
        formatted_payloads = new Set([...formatted_payloads, ...temp_results]);
      }
    }
  } catch (err) {
    console.error(`Error reading directory: ${err}`);
  }
  return Array.from(formatted_payloads);
}

// Function to read a file line by line
export async function readFileLineByLine(filePath, position, method, type) {
  let formatted_payloads = new Set();

  try {
    const data = fs.readFileSync(filePath, "utf8");
    const lines = data.split("\n");
    for (let y = 0; y < lines.length; y++) {
      let payload = lines[y];
      if (payload.length > 0) {
        let formatted_payload = await FormatPayload(position, method, payload, type);
        formatted_payloads.add(formatted_payload);
      }
    }
  } catch (err) {
    console.error(`Error reading file: ${err}`);
  }
  return formatted_payloads;
}



export async function TestSinglePayload(payload, position, method) {
  let formattedPayload = await FormatPayload(position, method, payload, PAYLOAD_TYPES.PAYLOAD);
  let result = await SendPayload(formattedPayload);
  if (result.resp_status == 403) {
    return true;
  } else {
    return false;
  }
}

export async function TestBusinessTraffic(businessTraffic, position, method, threads){
  let resultsStatistics = await Test(businessTraffic, position, method, PAYLOAD_TYPES.BUSINESS_TRAFFIC, threads);
  if ('200' in resultsStatistics.data && resultsStatistics.data['200'].length == resultsStatistics['total']) {
    return true;
  } else {
    return false;
  }
}

export async function TestPayloads(payloads, position, method, threads){
  let resultsStatistics = await Test(payloads, position, method, PAYLOAD_TYPES.PAYLOAD, threads)
  return resultsStatistics;
}

export default async function Test(data, position, method, type, threads) {
  let payloads = await formatPayloads(data,
    position,
    method,
    type);
  return await orchestrateAttack(type, payloads, threads);
}

/**
 * Create a common Axios configuration object
 * @param {Object} formattedPayload - formatted payload object
 */
function getAxiosConfiguration(formattedPayload) {
  let config = {
    timeout: 5000,
    raxConfig: {
      noResponseRetries: 3,
      retryDelay: 1000,
      backoffType: "exponential",
      statusCodesToRetry: [],
    },
  };
  if (formattedPayload.method == "GET") {
    config.params = formattedPayload.data;
  }
  // defaults to form url encoded
  if (formattedPayload.method == "POST") {
    config.headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  }
  // Seem to break axios
  // if (process.env["PROXY_HOST"] !== undefined && process.env["PROXY_PORT"] !== undefined && process.env["PROXY_PROTOCOL"] !== undefined) {
  //   config.proxy = {
  //       protocol: process.env["PROXY_PROTOCOL"],
  //       host: process.env["PROXY_HOST"],
  //       port: process.env["PROXY_PORT"],
  //     }
  // }
  return config;
}