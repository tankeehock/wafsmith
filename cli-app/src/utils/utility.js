import fs from 'fs';
import crypto from 'crypto';
import path from "path";
import {COLORS, MODSEC_RULE_ID_RANGE} from "./constants.js";
import chalk from 'chalk';

export function PrintToConsole(content, color){
  if (color == COLORS.RED) {
    console.log(chalk.red(content));
  } else if (color == COLORS.YELLOW) {
    console.log(chalk.yellow(content));
  } else if (color == COLORS.BLUE) {
    console.log(chalk.blue(content));
  } else if (color == COLORS.GREEN) {
    console.log(chalk.green(content));
  } else {
    // Defaults to terminal's defalt color
    console.log(content);
  }
}


/**
 * Utility function to slice the array into chunks
 * @returns {[]Array} - Arrays of arrays of payloads 
 */

export function SliceArrayIntoChunks(payloads, threads) {
    let numOfGroups = Math.min(threads, payloads.length);
    const result = [];
    const copiedPayloads = [...payloads];
    let i=0;
    for (;i<numOfGroups;i++) {
        result.push([]);
    }
    i=0;
    while(copiedPayloads.length > 0) {
        let payload = copiedPayloads.pop();
        result[i].push(payload);
        i++;
        if (i >= numOfGroups){
            i=0;
        }
    }
    return result;
}


export async function ReadAllFileContentInDirectory(directory) {
    let fileContent = [];
    let filePaths = await ListFilesInDirectory(directory);
    for (let i = 0; i < filePaths.length; i++) {
        let filePath = filePaths[i];
        let currentFileContent = await ReadFile(filePath);
        fileContent = [...fileContent, ...currentFileContent];
    }
    return fileContent;
}

export async function ListFilesInDirectory(directory) {
    let files = [];
    let directoryPath = directory;
    // Check if the path is absolute
    if (path.isAbsolute(directory)) {
      directoryPath = directory;
    } else {
      // If the path is relative, resolve it to an absolute path
      const baseDir = await process.cwd();
      directoryPath = path.resolve(baseDir, directory);
    }
    try {
      const fileNames = fs.readdirSync(directoryPath);
      for (const file of fileNames) {
        const filePath = path.join(directoryPath, file);
        const stats = fs.statSync(filePath);
        if (stats.isFile()) {
            files.push(filePath);
        }
      }
    } catch (err) {
      console.error(`Error reading directory: ${err}`);
    }
    return files;
  }

export function GetPercentageDisplay(current, total) {
    return `${(current / total * 100).toFixed(2)}`;
}

export function ReadFile(filePath) {
    try {
      return fs.readFileSync(filePath, 'utf8').split('\n');
    } catch (err) {
        return [];
    }
}

export function WriteLinesToFile(outputFile, payloads) {
    let content = payloads.join('\n');
    fs.writeFileSync(outputFile, content, (err) => {
        if (err) {
            console.error('Error writing file:', err);
        }
    });
}

export function GenerateRandomNumber(min,max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function generateSHA256Hash(input) {
    input += Date.now();
    return crypto.createHash('sha256').update(input).digest('hex');
}
export async function Sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

export async function URLDecodeNginxLogEntry(logEntry) {
    return decodeURIComponent(logEntry);
}

export async function UpdateModSecRuleId(rule) {
  const idRegex = /id:\d+,/;
 return rule.replace(idRegex, `id:${await GenerateRandomNumber(MODSEC_RULE_ID_RANGE.MIN,MODSEC_RULE_ID_RANGE.MAX)},`);
}

export async function RemoveDuplicateRules(rules) {
  let uniqueIDs = new Set();
  let uniqueRules = [];
  for(let i=0; i<rules.length; i++) {
    let rule = rules[i];
    const idMatch = rule.match(/id:(\d+)/);
    if (idMatch) {
        const id = idMatch[1];
        if (!uniqueIDs.has(id)) { // Check if the ID is already in the set
            uniqueIDs.add(id); // Add the ID to the set
            uniqueRules.push(rule); // Add the rule to the unique rules list
          }
    }
  }
  return uniqueRules;
}

async function modifyModSecRuleId(rule, newId) {
  const regex = /SecRule\s+(\S+)\s+"@(\S+)\s+([^"]+)"\s+"([^"]+)"/;
  const match = rule.match(regex);

  if (match) {
      const variable = match[1];
      const operator = match[2];
      const pattern = match[3];
      const actions = match[4].split(',');

      const modifiedActions = actions.map(action => {
          const [key, value] = action.split(':');
          if (key.trim() === 'id') {
              return `id:${newId}`; // Modify the ID
          }
          return action;
      });

      const modifiedRule = `SecRule ${variable} "@${operator} ${pattern}" "${modifiedActions.join(',')}"`;
      return modifiedRule;
  } else {
      return null;
  }
}
async function ParseModSecRule(rule) {
  const regex = /SecRule\s+(\S+)\s+"@(\S+)\s+([^"]+)"\s+"([^"]+)"/;
  const match = rule.match(regex);

  if (match) {
      const variable = match[1];
      const operator = match[2];
      const pattern = match[3];
      const actions = match[4].split(',');

      const parsedActions = await actions.reduce(async (acc, action) => {
          const [key, value] = action.split(':');
          acc[key.trim()] = value ? value.trim() : true;
          return acc;
      }, {});

      return {
          variable,
          operator,
          pattern,
          actions: parsedActions
      };
  } else {
      return null;
  }
}

async function Test() {
  let nginxLogs = ReadFile("/Users/bytedance/Workspace/TikTok-BitsCode/cognitive_ai_agent_waf_rule_management/agent-framework/data/logs/sample.log");
  const logEntry = '172.20.0.1 - - [14/Mar/2025:05:25:00 +0000] "GET /?payload=%3Cinput+type%3Dtext+value%3D%E2%80%9CXSS%E2%80%9D%3E HTTP/1.1" 200 13 "-" "axios/1.7.9" "-"';
  console.log(await URLDecodeNginxLogEntry(logEntry));
  for (let i=0; i<nginxLogs.length; i++) {
    let nginxLog = nginxLogs[i];
    console.log(await URLDecodeNginxLogEntry(nginxLog));
  }
  // let modSecRules = ReadFile("/Users/bytedance/Workspace/TikTok-BitsCode/cognitive_ai_agent_waf_rule_management/agent-framework/data/experiment/xss/output/rules/modsecurity-rules.conf");
  // console.log(modSecRules.length);
  // console.log(modSecRules);
  // let uniqueRules = await RemoveDuplicateRules(modSecRules);
  // console.log(uniqueRules.length);
  // console.log(uniqueRules);
  // let modSecRules = [
  //   `SecRule ARGS_GET "@rx (onpointerdown|onclose|onMouseEnter|onBeforeDeactivate|onprogress|ondragexit|onMoveStart|onCellChange|onpageshow|onbounce|onUnload|onLoseCapture|onAfterPrint|onresize|ondrop|onPaste|onControlSelect|onpointerout|oncut|onMouseOver|onBeforeUnload|onpaste|oncanplay|onMediaComplete|onAfterUpdate|onpopstate|ondragenter|onMoveEnd|onBounce|onscroll|ondurationchange|onPause|onCopy|onpointerrawupdate|ondrag|onBegin|onreset|ondragstart|onOutOfSync|onContextMenu|onpointerup|ondragend|onBlur|onrepeat|ondragover|onOnline|onClick|onpointerover|ondblclick|oncanplaythrough|onMediaError|onBeforeActivate|onratechange|ondragleave|onOffline|onChange|onpagehide|onblur|onUndo|onLoad|onActivate|ontransitionend|onloadedmetadata|onanimationend|onSeek|onFilterChange|onscrollend|onend|onPopState|onCut|onmozfullscreenchange|onbegin|onURLFlip|onLayoutComplete|onAbort|onselectionchange|onfocusin|onRepeat|onDeactivate|onpointerenter|oncontextmenu|onMouseLeave|onBeforeEditFocus|ontouchmove|onkeyup|onafterprint|onRowInserted|onEnd|onseeking|onfinish|onReadyStateChange|onDataSetComplete|onseeked|onerror|onPropertyChange|onDataSetChanged|onplaying|onclick|onmessage|onanimationstart|onSelectStart|onFocus|onpointermove|oncuechange|onMouseOut|onBeforePrint|ontransitioncancel|onloadeddata|onanimationcancel|onScroll|onErrorUpdate|onselectstart|onfocusout|onReset|onDrag|onsearch|onended|onProgress|onDataAvailable|onshow|onformdata|onResize|onDragDrop|onpointerleave|oncopy|onMouseMove|onBeforePaste|ontransitionrun|onloadstart|onanimationiteration|onSelect|onFinish|onselect|onfocus|onRedo|onDblClick|onunload|onmouseenter|onbeforecopy|onStart|onFocusOut|onvolumechange|onmouseleave|onbeforecut|onStop|onHashChange|onwebkittransitionend|onmouseup|onbeforetoggle|onTimeError|onKeyPress|ontoggle|onkeydown|onRowDelete|onDragStart|onsuspend|oninput|onResume|onDragLeave|onstart|onfullscreenchange|onResizeEnd|onDragEnd|ontouchend|onkeypress|onRowExit|onDrop|ontimeupdate|oninvalid|onReverse|onDragOver|onwebkitanimationiteration|onmouseout|onbeforeprint|onSubmit|onInput|onunhandledrejection|onmousedown|onauxclick|onSelectionChange|onFocusIn|onload|onafterscriptexecute|onRowsEnter|onError|onplay|onchange|onMessage|onBeforeCopy|onwebkitanimationstart|onmouseover|onbeforescriptexecute|onSyncRestored|onKeyDown|onwheel|onmousewheel|onbeforeunload|onTrackChange|onKeyUp|FSCommand|onsubmit|onhashchange|onResizeStart|onDragEnter|onwebkitanimationend|onmousemove|onbeforeinput|onStorage|onHelp)" "id:800286150,phase:2,deny,severity:2,tag:'Catch event handlers in GET URL parameters'"`,
  //   `SecRule ARGS_GET "@rx (&#x003C;|&#X000003C|&#0{0,3}60|&#X0003C;|&#060|&#X3C|&#X00003C|&#0060|&#X003C;|&#60|&#X0003C|&#060|&#X03C|&#x0{0,5}3C|&#x003c|&#x000003c|&#x3c|&#X00003c|&#x0003c|&#X03c|&#x00003c|&#x03c|&#X0003c|&#x0003c|&#X3c|&#x3C;|&#X00003c|&#x3C;|&#x3c|&#X003c)" "id:615376784,phase:2,deny,severity:2,tag:'Catch encoded HTML opening tag payload in GET parameters'"`,
  //   `SecRule ARGS_GET "@rx (<|</div>|</HTML>|</body>|</xsl:template>|</xmp>|</head>|</image>|</feImage>|</template>)" "id:990659791,phase:2,deny,severity:2,tag:'Catch HTML closing tags in GET URL parameters'"`,
  //   `SecRule ARGS_GET "@rx (<a class=bar href=\"http://www\.example\.org\">www\.example\.org</a>|<x%09onxxx=1|<x %6Fnxxx=1|<x on%78xx=1|<x/onxxx=1|<x onxxx%3D1|<x </onxxx=1|<x%0Conxxx=1|<x%2Fonxxx=1|<x%0Donxxx=1|<h1>Drop me</h1>|<h1>INJECTX</h1>|<body>|<body>Hello</body>|<circle fill=\"red\" r=\"40\"></circle>|<circle r=\"400\"></circle>|<div id=\"116\"><div id=\"x\">x</div>|<div id=\"123\"><span class=foo>Some text</span>|<div id=\"113\"><div id=\"x\">XXX</div>|<div id=\"131\"><b>drag and drop one of the following strings to the drop box:</b>|<div id=\"117\"><a href=\"http://attacker.org\">|<feImage>|<head>|<input type=\"submit\">|<math>)" "id:665544801,phase:1,deny,severity:2,tag:'Catch HTML payloads in GET URL parameters'"`
  //   ]
  // for (let i=0;i<modSecRules.length; i++) {
  //   console.log(modSecRules[i]);
  //   console.log(await UpdateModSecRuleId(modSecRules[i]));
  // }
}
// Test();
// await Test();