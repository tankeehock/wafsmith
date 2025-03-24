import fs from 'fs';
import path from 'path';
import {ReadAllFileContentInDirectory, ReadFile} from "./utility.js"
import OpenAI from 'openai/index.mjs';
import {CREATE_SYSTEM_PROMPT_1} from "../lib/llm/prompts/create.js";
import {AGGREGATE_SYSTEM_PROMPT_1} from "../lib/llm/prompts/aggregate.js";
import {EXTRACT_SYSTEM_PROMPT_1} from "../lib/llm/prompts/extract.js";
import {GenerateWorkflowClient} from "../lib/controller/workflow.js";
import {PrepareTestingEnvironment} from "../lib/tester/deployment.js";
import chalk from 'chalk';


export async function ValidateCreateCommand(input, options) {
    let result = await ValidateBaseCommand(options);
    await validateTestingRelatedCommand(result, input, options);
    await validateAIandModSecurityCommand(result, options, CREATE_SYSTEM_PROMPT_1);
    if (result.proceed) {
        await PrepareTestingEnvironment(result.setup);
    }
    return result;
}

export async function ValidateAggregateCommand(input, options) {
    let result = await ValidateBaseCommand(options);
    await validateTestingRelatedCommand(result, input, options);
    await validateAIandModSecurityCommand(result, options, AGGREGATE_SYSTEM_PROMPT_1);
    if (!ValidatePath(options.rules)) {
        result.errorMessages.push(`- Invalid rules path: ${options.rules}`);
        result.proceed = false;
    } else {
        result.rules = await GetContentFromPath(options.rules)
        result.configurationMessages.push(`- ${result.rules.length} rules found from ${options.rules}`);
    }
    if (result.proceed) {
        await PrepareTestingEnvironment(result.setup);
    }
    return result;
}

export async function ValidateEvaluateCommand(input, options) {
    let result = await ValidateBaseCommand(options);
    await validateTestingRelatedCommand(result, input, options);
    if (result.proceed) {
        await PrepareTestingEnvironment(result.setup);
    }
    return result;
}

export async function ValidateExtractCommand(input, options) {
    let result = await ValidateBaseCommand(options);
    if (!ValidatePath(input)) {
        result.errorMessages.push(`- Invalid logs path: ${input}`);
        result.proceed = false;
    } else {
        let logs = await GetContentFromPath(input);
        if(logs.length > 0) {
            result.logs = logs;
            result.configurationMessages.push(`- ${result.logs.length} log entries found from ${input}`);
        } else {
            result.errorMessages.push(`- No log entries found: ${input}`);
            result.proceed = false;
        }
    }
    if (!ValidateParentDirectory(options.output) || validateIfInputIsDirectory(options.output)) {
        result.errorMessages.push(`- Invalid output file path for the extract payloads: ${options.output}`);
        result.proceed = false;
    } else {
        result.outputPath = options.output
        result.configurationMessages.push(`- Extracted payload(s) will be written to ${result.outputPath}`);
    }

    if (!await checkOpenAIConfiguration(options.baseUrl, options.apiKey, options.model)) {
        result.errorMessages.push(`- Invalid OpenAI configurations`);
        result.proceed = false;
    } else {
        result.configurationMessages.push(`- LLM interactions will be made to ${options.baseUrl} using ${options.model}`);
        result.workflowClient = GenerateWorkflowClient(options.baseUrl, options.apiKey,EXTRACT_SYSTEM_PROMPT_1,options.model);
    }
    return result;
}
async function validateAIandModSecurityCommand(result, options, prompt) {
    if (!await checkOpenAIConfiguration(options.baseUrl, options.apiKey, options.model)) {
        result.errorMessages.push(`- Invalid OpenAI configurations`);
        result.proceed = false;
    } else {
        result.configurationMessages.push(`- LLM interactions will be made to ${options.baseUrl} using ${options.model}`);
        result.workflowClient = GenerateWorkflowClient(options.baseUrl, options.apiKey,prompt,options.model);
    }
    if (!ValidateParentDirectory(options.output) || validateIfInputIsDirectory(options.output)) {
        result.errorMessages.push(`- Invalid output file path for generated ModSecurity rules: ${options.output}`);
        result.proceed = false;
    } else {
        result.outputPath = options.output
        result.configurationMessages.push(`- ModSecurity rules will be written to ${result.outputPath}`);
    }
}

async function validateTestingRelatedCommand(result, input, options) {
    result.method = options.method;
    result.position = options.position;
    result.target = options.target;
    if (!ValidatePath(options.traffic)) {
        result.configurationMessages.push(`- No traffic file specified, skipping business traffic simulation.`);
    } else {
        result.traffic = await GetContentFromPath(options.traffic)
        result.configurationMessages.push(`- ${result.traffic.length} traffic payload(s) found from ${options.traffic}`);
        result.configurationMessages.push(`- Traffic content will be sent as ${options.method} requests and positioned in the ${options.position} segment of the request.`);
    }

    if (!ValidateParentDirectory(options.evaded)) {
        result.errorMessages.push(`- Invalid output file path for evaded payload(s): ${options.evaded}`);
        result.proceed = false;
    } else {
        result.evadedPath = options.evaded
        result.configurationMessages.push(`- Evaded payload(s) will be written to ${result.evadedPath}`);
    }

    if (!validateDockerSetup(options.setup)) {
        result.errorMessages.push(`- docker-compose.yml not found in ${options.setup}`);
        result.proceed = false;
    } else {
        result.setup = options.setup;
        result.configurationMessages.push(`- docker-compose.yml will be invoked from ${options.setup}`);
    }

    if (!ValidatePath(input)) {
        result.errorMessages.push(`- Invalid payload path: ${input}`);
        result.proceed = false;
    } else {
        result.payloads = await GetContentFromPath(input)
        result.configurationMessages.push(`- ${result.payloads.length} payload(s) found from ${input}`);
        result.configurationMessages.push(`- Payload(s) will be sent as ${options.method} requests and positioned in the ${options.position} segment of the request.`);
    }
}

async function ValidateBaseCommand(options) {
    let result = {
        'proceed': true,
        'errorMessages': [],
        'configurationMessages': [],
    }

    result.threads = options.threads;
    result.configurationMessages.push(`- ${result.threads} threads will be used for execution`); //remove
    return result;
}

export function validateDockerSetup(setupPath) {
    if (ValidatePath(setupPath) && validateIfInputIsDirectory(setupPath)) {
        let dockerPath = path.join(setupPath, 'docker-compose.yml');
        if (ValidatePath(dockerPath)) {
            return true;
        }else {
            return false;
        }
    } else {
        return false;
    }
}

export async function GetContentFromPath(inputPath) {
    if (ValidatePath(inputPath)) {
        if (validateIfInputIsDirectory(inputPath)) {
            return await ReadAllFileContentInDirectory(inputPath)
        } else {
            return await ReadFile(inputPath);
        }
    }
}

async function checkOpenAIConfiguration(endpoint, apiKey, model) {
    // Initialize OpenAI configuration
    // try {
    //     let client = new OpenAI({
    //         apiKey: apiKey,
    //         baseURL: endpoint,
    //       });
    //     const completion = await client.chat.completions.create({
    //         messages: [
    //             { role: 'system', content: "You are a cybersecurity expert!" },
    //             { role: "user", content: "Is MD5 secure?" }
    //         ],
    //         model: model
    //         }
    //     )
    //     const assistantResponse = completion.choices[0]?.message?.content;
    //     return true;
    // } catch (err) {
    //     return false;
    // }
    return true; // speed up dev
}

export function ValidateParentDirectory(filePath) {
    try {
        const parentDir = path.dirname(filePath);
        if (fs.existsSync(parentDir)) { 
            return true;
        } else {
            return false;
        }
    } catch (err) {
        return false;
    }
}

export function ValidatePath(path) {
    try {
        if (fs.existsSync(path)) {
            return true;
        } else {
            return false;
        }
    } catch (err) {
        return false;
    }
}

export function validateIfInputIsDirectory(filePath) {
    try {
        const stats = fs.statSync(filePath);
        if (stats.isDirectory()) {
            return true;
        } else {
            return false;
        }
    } catch (err) {
        return false;
    }
}

export default async function DisplayValidationMessages(config) {
    if (!config.proceed) {
        console.log(chalk.red("Error(s) found the given input(s):"));
        for (const errorMessage of config.errorMessages) {
          console.log(chalk.red(errorMessage));
        }
        console.log(chalk.red("LWRC will not proceed with the execution."));
        process.exit(1);
    }
    console.log(chalk.yellow("Execution Configuration(s)"));
    for (let configurationMessage of config.configurationMessages) {
        console.log(chalk.yellow(configurationMessage));
    }
}