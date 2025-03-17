import { Command, Argument } from 'commander';
import {EvaluateWorkflow} from '../lib/controller/workflow.js';
import DisplayValidationMessages, {ValidateEvaluateCommand} from "../utils/validator.js";
import { PAYLOAD_POSITION, HTTP_METHOD, DEFAULT_NUM_THREADS } from '../utils/constants.js';
import ora from 'ora';
const Evaluate = new Command('evaluate');

Evaluate
  .description('Evaluate deployed WAF rules against a list of payloads')
  .addArgument(new Argument('<payload-directory>', 'Input directory / file containing the payloads'))
  .requiredOption('-e, --evaded <evaded-file>', 'Specify the output file for evaded payload(s) if any')
  .requiredOption('-s, --setup <setup-directory>', 'Specify the directory which contains the docker compose enviornment setup')
  .requiredOption('-t, --traffic <traffic>', 'Specify directory / file containing business traffic content for simulation')
  .option('-p, --position <position>', `Specify the postion of the payload in the HTTP request. Default is ${PAYLOAD_POSITION.URL_PARAMETERS}`, PAYLOAD_POSITION.URL_PARAMETERS)
  .option('-m, --method <method>', `Specify the HTTP method for the payload. Default is ${HTTP_METHOD.GET}.`, HTTP_METHOD.GET)
  .option('-x, --threads <threads>', `Specify the number of threads to be used during the rule generation process. Default is ${DEFAULT_NUM_THREADS}`, DEFAULT_NUM_THREADS)
  .action(async (input, options) => {
    let spinner = ora(`Validating CLI arguments and preparing testing enviornment...`).start();
    let config = await ValidateEvaluateCommand(input, options);
    spinner.stop();
    await DisplayValidationMessages(config);
    console.time("Evaluate WAF Rules");
    await EvaluateWorkflow(config.setup, config.payloads, config.traffic, config.position, config.method, config.evadedPath, config.threads);
    console.timeEnd("Evaluate WAF Rules");
});

export default Evaluate;