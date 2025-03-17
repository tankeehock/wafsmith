import { Command, Argument } from 'commander';
import {RuleGenerationWorkflow, GenerateWorkflowClient} from '../lib/controller/workflow.js';
import chalk from 'chalk';
import { PAYLOAD_POSITION, HTTP_METHOD, DEFAULT_NUM_THREADS, COLORS } from '../utils/constants.js';
import {ValidateCreateCommand} from '../utils/validator.js';
import {PrintToConsole} from '../utils/utility.js';
import ora from 'ora'
const Create = new Command('create');

Create
  .description('Create ModSecurity Rules')
  .addArgument(new Argument('<input>', 'Input directory / file containing the payloads'))
  .requiredOption('-o, --output <output-file>', 'Specify the output file for the newly generated rule(s) if any')
  .requiredOption('-e, --evaded <evaded-file>', 'Specify the output file for evaded payload(s) if any')
  .requiredOption('-s, --setup <setup-directory>', 'Specify the directory which contains the docker compose enviornment setup')
  .requiredOption('-t, --traffic <traffic>', 'Specify directory / file containing business traffic content for simulation')
  .requiredOption('-k, --api-key <key>', 'OpenAI API Key')
  .requiredOption('-b, --base-url <base>', 'OpenAI SDK Endpoint')
  .requiredOption('-l, --model <model>', 'OpenAI Model')
  .option('-p, --position <position>', `Specify the postion of the payload in the HTTP request. Default is ${PAYLOAD_POSITION.URL_PARAMETERS}`, PAYLOAD_POSITION.URL_PARAMETERS)
  .option('-m, --method <method>', `Specify the HTTP method for the payload. Default is ${HTTP_METHOD.GET}.`, HTTP_METHOD.GET)
  .option('-x, --threads <threads>', `Specify the number of threads to be used during the rule generation process. Default is ${DEFAULT_NUM_THREADS}`, DEFAULT_NUM_THREADS)
  .action(async (input, options) => {
    let spinner = ora(`Validating CLI arguments and preparing testing enviornment...`).start();
    let config = await ValidateCreateCommand(input, options);
    spinner.stop();
    if (!config.proceed) {
        PrintToConsole("Error(s) found the given input(s):", COLORS.RED);
        for (const errorMessage of config.errorMessages) {
          PrintToConsole(errorMessage, COLORS.RED);
        }
        PrintToConsole("LWRC will not proceed with the execution.", COLORS.RED);
        process.exit(1);
    }
    PrintToConsole("Execution Configuration(s)", COLORS.YELLOW);
    for (let configurationMessage of config.configurationMessages) {
      PrintToConsole(configurationMessage, COLORS.YELLOW);
    }

    console.time("Create ModSecurity Rules");
    await RuleGenerationWorkflow(config.workflowClient, config.setup, config.traffic, config.payloads, config.method, config.position, config.outputPath, config.evadedPath, config.threads);
    console.timeEnd("Create ModSecurity Rules");
  });

export default Create;