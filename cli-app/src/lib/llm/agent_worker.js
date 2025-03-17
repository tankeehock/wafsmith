
import { parentPort} from "worker_threads";
import {CreateModSecurityRule} from "./agent.js";
import {GenerateOpenAIClient} from "../controller/workflow.js";

// Listen for messages from the main thread
parentPort.on('message', async (data) => {
    let results = [];
    // console.log("----------- inside agent worker");
    // console.log("data",data);
    for (let i = 0; i < data.payloads.length; i++) {
        // Ensures that the conversation is new for every rule
        let openAIClient = await GenerateOpenAIClient(data.workflowClient.openAPIEndpoint, data.workflowClient.token, data.workflowClient.systemPrompt, data.workflowClient.model);
        let rule = await CreateModSecurityRule(openAIClient, data.payloads[i], data.method, data.position);
        results.push({
            rule: rule,
            payload: data.payloads[i]
        });
    }
    parentPort.postMessage(results);
    process.exit(0);
  });
  