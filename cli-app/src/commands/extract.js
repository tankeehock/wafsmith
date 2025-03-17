import { Command, Argument } from 'commander';
import {PayloadExtractionWorkflow} from '../lib/controller/workflow.js';
import chalk from 'chalk';
import { COLORS, DEFAULT_NUM_THREADS } from '../utils/constants.js';
import {PrintToConsole} from '../utils/utility.js';
import {ValidateExtractCommand} from '../utils/validator.js';
import ora from 'ora'
const Extract = new Command('extract');


// TO TEST
Extract
  .description('Extract payload(s) from logs')
  .addArgument(new Argument('<input>', 'Input directory / file containing the Nginx log files'))
  .requiredOption('-o, --output <output-file>', 'Specify the output file for the newly generated rule(s) if any')
  .requiredOption('-k, --api-key <key>', 'OpenAI API Key')
  .requiredOption('-b, --base-url <base>', 'OpenAI SDK Endpoint')
  .requiredOption('-l, --model <model>', 'OpenAI Model')
  .option('-x, --threads <threads>', `Specify the number of threads to be used during the rule generation process. Default is ${DEFAULT_NUM_THREADS}`, DEFAULT_NUM_THREADS)
  .action(async (input, options) => {
    let spinner = ora(`Validating CLI arguments and preparing testing enviornment...`).start();
    let config = await ValidateExtractCommand(input, options);
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

    console.time("Extract Malicious Payloads from Logs");
    await PayloadExtractionWorkflow(config.workflowClient, config.logs, config.outputPath, options.threads);
    console.timeEnd("Extract Malicious Payloads from Logs");
  });

export default Extract;