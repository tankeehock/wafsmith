import {CREATE_USER_PROMPT_1, CREATE_USER_PROMPT_1_RETRY, CREATE_USER_PROMPT_2} from './prompts/create.js'
import {EXTRACT_USER_PROMPT_1} from "./prompts/extract.js";
import {AGGREGATE_USER_PROMPT_1} from './prompts/aggregate.js';
import {SliceArrayIntoChunks, GenerateRandomNumber} from "../../utils/utility.js";
import { Worker } from "worker_threads";

export async function ContinueConversation(openAIClient, newUserInput) {
  openAIClient.conversationHistory.push({ role: "user", content: newUserInput });
  const completion = await openAIClient.client.chat.completions.create({
    messages: openAIClient.conversationHistory,
    model: openAIClient.model
  });
  const assistantResponse = completion.choices[0]?.message?.content;
  openAIClient.conversationHistory.push({ role: "assistant", content: assistantResponse });
  // return conversationHistory;
}

function checkForValidJSONString(jsonString) {
  try {
    JSON.parse(jsonString);
    return true;
  } catch(err) {
    return false;
  }
}

function testRegularExpression(regularExpression, payload) {
  try {
    let regex = new RegExp(regularExpression);
    let validRegularExpression = false;
    if (regex.test(payload)) {
      validRegularExpression = true;
    }
    return validRegularExpression;
  } catch (err) {
    return false;
  }
}

async function executePrompt1(openAIClient, payload) {
  let user_prompt_1 = CREATE_USER_PROMPT_1.replace("%%PAYLOAD%%", payload);
  await ContinueConversation(openAIClient, user_prompt_1);
  let regexPattern = openAIClient.conversationHistory[openAIClient.conversationHistory.length - 1].content;
  let validRegularExpression = testRegularExpression(regexPattern, payload);
  let retries = 2;
  while (validRegularExpression == false && retries > 0) {
    await ContinueConversation(openAIClient, CREATE_USER_PROMPT_1_RETRY);
    regexPattern = openAIClient.conversationHistory[openAIClient.conversationHistory.length-1].content;
    validRegularExpression = testRegularExpression(regexPattern, payload);
    retries--;
  }
  return validRegularExpression;
}

async function executePrompt2(openAIClient, method, position) {
  let user_prompt_2 = CREATE_USER_PROMPT_2.replace("%%POSITION%%", position);
  user_prompt_2 = user_prompt_2.replace("%%METHOD%%", method);
  user_prompt_2 = user_prompt_2.replace("%%ID%%", GenerateRandomNumber(100000000,999999999));
  await ContinueConversation(openAIClient, user_prompt_2);
  let modeSecurityRule = openAIClient.conversationHistory[openAIClient.conversationHistory.length-1].content;
  return modeSecurityRule;
}

// Create a multi-threaded CreateModSecurityRules function 
export async function CreateModSecurityRules(workflowClient, payloads, method, position, numberOfThreads){
  let results = [];
  let workers = [];
  let numWorkers = Math.min(numberOfThreads, payloads.length);
  let completedWorkers = 0;
  let chunks = SliceArrayIntoChunks(payloads, numWorkers);
  // Function to handle worker completion
  const handleWorkerCompletion = async () => {
    completedWorkers++;
  };
  for (let i = 0; i < numWorkers && i < payloads.length; i++) {
    // Send data to the worker
    const worker = new Worker(import.meta.dirname + "/agent_worker.js");
    worker.postMessage({ workflowClient: workflowClient, payloads: chunks[i], method: method, position: position });
    // Receive data from the worker
    worker.on("message", (result) => {
      // [{rule,payload}, {rule,payload}]
      results = [...results, ...result];
    });
    worker.on("exit", handleWorkerCompletion);
    // Handle errors
    worker.on("error", (err) => {
      // console.log(err.stack);
      completedWorkers++;
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

export async function CreateModSecurityRule(openAIClient, payload, method, position) {
  let validRegularExpression = await executePrompt1(openAIClient, payload);
  if (!validRegularExpression) {
    return null;
  }
  let modSecurityRule = await executePrompt2(openAIClient, method, position);
  // find ways to check for mod security rule syntax
  // breaks the entire execution easily if it is not valid
  return modSecurityRule;
}

async function executeAggregatePrompt1(openAIClient, rules, businessTraffic) {
  let user_prompt_1 = AGGREGATE_USER_PROMPT_1.replace("%%MODSECURITY_RULES%%", rules);
  user_prompt_1 = user_prompt_1.replace("%%BUSINESS_TRAFFIC%%", businessTraffic);
  await ContinueConversation(openAIClient, user_prompt_1);
  let generatedRules = openAIClient.conversationHistory[openAIClient.conversationHistory.length - 1].content;
  return generatedRules.split(/\r?\n/);
}

export async function AggregateModSecurityRules(openAIClient, rules, businessTraffic) {
  let aggregatedRules = await executeAggregatePrompt1(openAIClient, rules, businessTraffic);
  return aggregatedRules;
}

async function executeExtractPrompt1(openAIClient, log) {
  let user_prompt_1 = EXTRACT_USER_PROMPT_1.replace("%%LOG%%", log);
  await ContinueConversation(openAIClient, user_prompt_1);
  let retries = 2;
  
  let jsonClassificationString = openAIClient.conversationHistory[openAIClient.conversationHistory.length - 1].content;
  let isJSON = checkForValidJSONString(jsonClassificationString);
  while(!isJSON && retries > 0) {
    await ContinueConversation(openAIClient, CREATE_USER_PROMPT_1_RETRY);
    jsonClassificationString = openAIClient.conversationHistory[openAIClient.conversationHistory.length - 1].content;
    isJSON = checkForValidJSONString(jsonClassificationString);
    retries--;
  }
  if (isJSON) {
    return JSON.parse(jsonClassificationString);
  } else {
    return null;
  }
}

export async function ExtractSuspiciousPayload(openAIClient, log) {
  // depending on the LLM models used, they may attempt to decode.
  log = decodeURIComponent(log); 
  let classification = await executeExtractPrompt1(openAIClient, log);
  return classification;

}

// Create a multi-threaded log classification function 
export async function ClassifyLogs(workflowClient, logs, numberOfThreads){
  let results = [];
  let workers = [];
  let numWorkers = Math.min(numberOfThreads, logs.length);
  let completedWorkers = 0;
  let chunks = SliceArrayIntoChunks(logs, numWorkers);

  // Function to handle worker completion
  const handleWorkerCompletion = async () => {
    completedWorkers++;
  };
  for (let i = 0; i < numWorkers; i++) {
    // Send data to the worker
    const worker = new Worker(import.meta.dirname + "/extract_worker.js");
    worker.postMessage({ workflowClient: workflowClient, logs: chunks[i]});
    // Receive data from the worker
    worker.on("message", (result) => {
      // [{log,classification}, {log,classification}]
      results = [...results, ...result];
    });
    worker.on("exit", handleWorkerCompletion);
    // Handle errors
    worker.on("error", (err) => {
      // console.log(err.stack);
      completedWorkers++;
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