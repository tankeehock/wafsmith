import { execSync } from 'child_process';
import fs from 'fs';
import {generateSHA256Hash, Sleep, ListFilesInDirectory} from '../../utils/utility.js';
import {DOCKER_SERVICES} from "../../utils/constants.js";
import path from 'path';

export async function DeleteModSecurityRuleFile(filePath) {
    try {
        fs.unlinkSync(filePath);
        return true;
    } catch (error) {
        console.error(`Error deleting ModSecurity rule file: ${error.message}`);
        return false;
    }
}

export async function WriteModSecurityRuleFile(directory, modSecurityRule) {
    try {
        let modSecurityRulesDirectory = path.join(directory, "rules");
        let fileName = "lwrc-"+ generateSHA256Hash(modSecurityRule) + ".conf"
        let filePath = path.join(modSecurityRulesDirectory, fileName);
        fs.writeFileSync(filePath, modSecurityRule, 'utf8');
        return filePath;
    } catch (error) {
        // console.log(err.stack());
        // console.log('unable to write modsecurity rule file', error);
        return "";
    }
}

export async function RedeployCRSContainer(path) {
    // TODO check if container can be deployed
    let command = `cd ${path} && docker compose restart crs-nginx`;
    await ExecuteCommand(command);
}

export async function DeployTestingEnviornment(path) {
    let command = `cd ${path} && docker compose up -d`;
    await ExecuteCommand(command);
}

export async function TeardownTestingEnviornment(path) {
    let command = `cd ${path} && docker compose down`;
    await ExecuteCommand(command);
}

export async function IsCreatedModSecurityRuleFile(filePath) {
    let regex = new RegExp(/.*(lwrc-.*\.conf)$/);
    if (regex.test(filePath)) {
      return true;
    } else {
        return false;
    }
}

export async function PrepareTestingEnvironment(setup) {
    let modSecurityRulesDirectory = path.join(setup, "rules");
    let files = await ListFilesInDirectory(modSecurityRulesDirectory);
    for (let i=0; i<files.length; i++) {
        let filePath = files[i];
        if (await IsCreatedModSecurityRuleFile(filePath)) {
            await DeleteModSecurityRuleFile(filePath);
        }
    }
    await TeardownTestingEnviornment(setup);
}

export async function ValidateModSecurityRuleInExistingContainers(setup, rule) {
    // console.log("ValidateModSecurityRuleInExistingContainers", "setup:",setup,"rule:",rule);
    let filePath = await WriteModSecurityRuleFile(setup, rule);
    await RedeployCRSContainer(setup);
    let isValidModSecurityRule = await CheckNGINXServiceStatus(setup);
    await DeleteModSecurityRuleFile(filePath);
    // console.log("validating:",rule, "isValidModSecurityRule:",isValidModSecurityRule)
    return isValidModSecurityRule;
}

export async function CheckNGINXServiceStatus(path) {
    return await CheckContainerHealth(path, DOCKER_SERVICES.NGINX);
}

export async function CheckContainerHealth(path, container) {
    let command = `cd ${path} && docker compose exec ${container} id`;
    let output = await ExecuteCommandWithOutput(command);
    const re = new RegExp(/(.*(\(nginx\)).*){3}/);
    if (re.test(output)) {
        return true;
    } else {
        return false;
    }
}

export async function ExecuteCommandWithOutput(command) {
    try {
        // console.log("\nEXECUTING COMMAND --------------------------------------------------------------------");
        // console.log("executing:", command);
        let output = (execSync(command, {stdio : 'pipe' })).toString();
        // console.log("output:", output);
        // console.log("EXECUTING COMMAND --------------------------------------------------------------------\n");
        await Sleep(1500);
        return output;
    } catch (err) {
        // console.log(err.stack);
        return "";
    }
}

export async function ExecuteCommand(command) {
    try {
        // const stdout = execSync(command, { stdio: 'inherit' });
        execSync(command, { stdio: 'pipe' });
        // console.log(`Command executed: ${command}`);
        // wait for docker to execute otherwise it will lead to docker container breaking later on
        await Sleep(1500);
        return true;
    } catch (err) {
        return false;
    }
}
// console.log(await DeleteModSecurityRuleFile("infra/rules/Users/bytedance/Workspace/TikTok-BitsCode/cognitive_ai_agent_waf_rule_management/agent-framework/cli-app/infra/rules/lwrc-44cb3d93dc01d9d60b16aa6e26f028757db1fd71bc6f5287ab9e005320fb29d9.conf"));
// await RedeployCRSContainer("./infra");
// console.log(await CheckNGINXServiceStatus("./infra"));