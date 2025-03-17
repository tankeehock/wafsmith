
import { parentPort} from "worker_threads";
import { SendPayload } from "./tester.js";

// Listen for messages from the main thread
parentPort.on('message', async (data) => {
    let results = [];
    for (let i = 0; i < data.formattedPayloads.length; i++) {
        try {
            let result = await SendPayload(data.formattedPayloads[i]);
            results.push(result);
        } catch (err) {
            console.error(`Error sending payload: ${err.stack}`);
        }
        
    }
    parentPort.postMessage(results);
    process.exit(0);
  });
  