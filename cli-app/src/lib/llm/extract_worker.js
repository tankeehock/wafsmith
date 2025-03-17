
import { parentPort} from "worker_threads";
import {ExtractSuspiciousPayload} from "./agent.js";
import {GenerateOpenAIClient} from "../controller/workflow.js";

// Listen for messages from the main thread
parentPort.on('message', async (data) => {
    let results = [];
    for (let i = 0; i < data.logs.length; i++) {
        // Ensures that the conversation is new for every rule
        let openAIClient = await GenerateOpenAIClient(data.workflowClient.openAPIEndpoint, data.workflowClient.token, data.workflowClient.systemPrompt, data.workflowClient.model);
        let classification = await ExtractSuspiciousPayload(openAIClient, data.logs[i]);
        results.push({
            log: data.logs[i],
            classification: classification,
        });
    }
    parentPort.postMessage(results);
    process.exit(0);
  });
  