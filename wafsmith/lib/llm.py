from typing import Dict, Any, Tuple, List
from openai import OpenAI
import traceback
from wafsmith.lib.models import Classification
from wafsmith.lib.payload import PayloadLocation
import wafsmith.lib.prompts.aggregate as PROMPT_AGGREGATE
from wafsmith.utils.helper import Utility
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
import wafsmith.lib.prompts.create as PROMPT_CREATE
import wafsmith.lib.prompts.extract as PROMPT_EXTRACT
import wafsmith.utils.constants as Constant
import multiprocessing
import logging

logger = logging.getLogger("llm")

class LLMAgent(BaseModel):
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    client: Any = None

    def setup(self):
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
    def prompt_agent(self, conversation, prompt):
        conversation.append({
            "role": "user",
            "content": prompt
        })

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=conversation
        )
        conversation.append({
            "role": "assistant",
            "content": completion.choices[0].message.content
        })
        logger.debug(f"llm_response={completion.choices[0].message.content}")
        return completion.choices[0].message.content


def classify_log(args: [LLMAgent, str, str]) -> Classification:
    classification = None
    try:
        conversation_history = [{
            "role": "system",
            "content": PROMPT_EXTRACT.SYSTEM_PROMPT
        }]
        llm_agent, log, message = args
        classification_response = llm_agent.prompt_agent(conversation_history, PROMPT_EXTRACT.USER_PROMPT_1.replace("%%LOG%%", log))
        classification = Utility.convert_raw_log_classifion_output_to_classication_object(classification_response)
        if not isinstance(classification, Classification):
            classification = None
    except Exception as e:
        logger.error(f"Error {message}: {e}")
    return classification

def classify_logs_in_parrallel(
    llm_agent: LLMAgent, 
    logs: List[str], 
    threads: int,
    message: str = "classify logs") -> List[Classification]:
    classifications = []

    """Process multiple payloads in parallel using threading.

    Args:
        LLMAgent: LLM Agent to perform the task
        logs: Logs
        threads: Number of threads to use
        message: Message to use in logs

    Returns:
        List containing the dictionary of the classification results
    """

    # Prepare arguments for parallel processing
    args = [(llm_agent, log, message) for log in logs]

    # Use ThreadPoolExecutor for parallel processing (better for I/O bound tasks)
    max_workers = min(
        threads, multiprocessing.cpu_count() * 2
    )  # More threads for I/O bound tasks
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for result in executor.map(classify_log, args):
            if result != None:
                classifications.append(result)
    return classifications

def aggregate_modsecurity_rules(llm_agent: LLMAgent, ruleset: List[str], business_traffic: List[str]) -> List[str]:
    aggregated_ruleset = []
    try:
        conversation_history = [{
            "role": "system",
            "content": PROMPT_AGGREGATE.SYSTEM_PROMPT
        }]
        modsecurity_rules = "\n".join(ruleset)
        business_traffic = "\n".join(business_traffic)
        prompt = PROMPT_AGGREGATE.USER_PROMPT_1.replace("%%MODSECURITY_RULES%%", modsecurity_rules)
        prompt = prompt.replace("%%BUSINESS_TRAFFIC%%", business_traffic)
        modsecurity_rules = llm_agent.prompt_agent(conversation_history, prompt)
        aggregated_ruleset = modsecurity_rules.split("\n")
    except Exception as e:
        logger.debug(traceback.format_exc())
        logger.error(f"Error aggregating rules: {e}")
    return aggregated_ruleset
def create_modsecurity_rule(args: Tuple[LLMAgent, str, str, PayloadLocation, str]) -> (str, str):
    modSecurityRule = None
    try:
        conversation_history = [{
            "role": "system",
            "content": PROMPT_CREATE.SYSTEM_PROMPT
        }]
        llm_agent, payload, method, position, message = args
        is_valid_regular_expression = False
        expression = llm_agent.prompt_agent(conversation_history, PROMPT_CREATE.USER_PROMPT_1.replace("%%PAYLOAD%%", payload))
        is_valid_regular_expression = Utility.validate_regular_expression(expression, payload)
        if not is_valid_regular_expression:
            attempts = 1
            while attempts < Constant.LLM_API_RETRIES:
                expression = llm_agent.prompt_agent(conversation_history, PROMPT_CREATE.USER_PROMPT_1_RETRY)
                is_valid_regular_expression = Utility.validate_regular_expression(expression, payload)
                if is_valid_regular_expression:
                    break
                else:
                    attempts += 1 
        
        if is_valid_regular_expression:
            # continue to create the mod security rule
            modsecurity_prompt = PROMPT_CREATE.USER_PROMPT_2.replace("%%METHOD%%", method)
            modsecurity_prompt = modsecurity_prompt.replace("%%POSITION%%", position.name)
            modsecurity_prompt = modsecurity_prompt.replace("%%ID%%", str(Utility.generate_random_modsecurity_id()))
            modSecurityRule = llm_agent.prompt_agent(conversation_history, modsecurity_prompt)
        else:
            # unable to create mod security rule after repeated attempts
            # return None
            pass
    except Exception as e:
        logger.error(f"Error {message}: {e}")
    return (payload, modSecurityRule)
def create_modsecurity_rules_in_parrallel(
    llmClient: LLMAgent,
    payloads: list[str],
    method: str,
    location: PayloadLocation,
    threads: int,
    message: str = "create modsecurity rules"
) -> Dict[str, str]:
    """Process multiple payloads in parallel using threading.

    Args:
        payloads: List of payload strings to process
        method: HTTP method to use
        location: Location enum value
        threads: Number of threads to use
        message: Message to use in logs

    Returns:
        Dictionary newly created ModSecurity Rules by LLM Agent mapped using the payload value as key
    """
    results = {}

    # Prepare arguments for parallel processing
    args = [(llmClient, p, method, location, message) for p in payloads]

    # Use ThreadPoolExecutor for parallel processing (better for I/O bound tasks)
    max_workers = min(
        threads, multiprocessing.cpu_count() * 2
    )  # More threads for I/O bound tasks
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for result in executor.map(create_modsecurity_rule, args):
            results[result[0]] = result[1]
    return results