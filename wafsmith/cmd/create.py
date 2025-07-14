import sys
import time
import logging
import traceback
from wafsmith.lib.console import console
from wafsmith.cmd.config import EvaluateConfig
from wafsmith.cmd.evaluate import evaluate_single_modsecurity_rule_with_payload, evaluate_single_modsecurity_rule_with_multiple_payloads
from wafsmith.lib.llm import aggregate_modsecurity_rules, create_modsecurity_rules_in_parrallel
from wafsmith.lib.env import TestingEnv
from wafsmith.lib.payload import PayloadLocation
from typing import List, Dict, Any, Tuple

from wafsmith.utils.helper import Utility
from wafsmith.utils.constants import DEFAULT_HOST

logger = logging.getLogger("create")

def run(
    payloads_dir: str,
    evaded_file: str,
    rules_file: str,
    setup_dir: str,
    traffic_path: str,
    position: str,
    method: str,
    threads: int,
    api_key: str,
    base_url: str, 
    model: str,
    host: str = DEFAULT_HOST,
):
    logger.info("Validating CLI arguments")

    config = EvaluateConfig(
        setup_dir=setup_dir,
        output_evaded_path=evaded_file,
        output_rules_path=rules_file,
        attack_payloads_dir=payloads_dir,
        traffic_payloads_dir=traffic_path,
        position=position,
        method=method,
        threads=threads,
        host=host,
        api_key=api_key,
        base_url=base_url,
        model=model
    )
    if not config.validateCreateConfig():
        logger.error("Configuration validation failed.")
        return

    logger.info("Validation complete.")

    try:
        config.load()
        config.loadLLMService()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return

    logger.info("Create WAF Rules")
    start_time = time.time()

    create(config)

    end_time = time.time()
    logger.info(f"Create WAF Rules: {end_time - start_time:.2f}s")

# TODO
def calculate_results(results: Dict[str, Any], expected_code: int = 200) -> Tuple[int, int, float, bool]:
    """Calculate statistics from results.
    
    Args:
        results: Results dictionary with 'total' and 'data' keys
        expected_code: Expected status code for success
        
    Returns:
        Tuple of (matched_count, total_count, percentage, all_passed)
    """
    matched_count = len(results["data"].get(expected_code, []))
    total_count = results["total"]
    percentage = (matched_count / total_count * 100) if total_count > 0 else 0
    all_passed = matched_count == total_count
    
    return matched_count, total_count, percentage, all_passed

# TODO
def write_results_to_file(file_path: str, payloads: List[str]) -> None:
    """Write payloads to a file.
    
    Args:
        file_path: Path to write to
        payloads: List of payload strings to write
    """
    with open(file_path, "w") as f:
        for payload in payloads:
            f.write(f"{payload}\n")
    logger.info(f"Written payloads to {file_path}")

# TODO
def create(config: EvaluateConfig):
    logger.info("Starting evaluation workflow")
    step = 1
    total_steps = 7
    try:
        # Step 1: Deploy Testing Evniornment
        with console.status("Deploying testing environment..."):
            testing_env = TestingEnv(base_dir=config.setup_dir)
            testing_env.setup()
            time.sleep(2)  # Give some time for the environment to start
        logger.info(f"[{step}/{total_steps}] Deployed testing environment")
        step += 1
        # Step 2: Create Rules
        rules_tracker = {} # Maps Payload to each individually created rule
        location: PayloadLocation = {
            "http_header": PayloadLocation.HTTP_HEADER,
            "http_body": PayloadLocation.HTTP_BODY,
        }.get(config.position, PayloadLocation.URL_PARAMETERS)
        with console.status("Creating waf rule(s)..."):
            rules_tracker = create_modsecurity_rules_in_parrallel(
                config.llm_agent,
                config.attack_payloads,
                config.method,
                location,
                config.threads,
                "create waf rule"
            )
        num_payloads, num_of_rules = Utility.count_created_rules(rules_tracker)
        logger.info(f"{num_of_rules} WAF rules created for {num_payloads} of payloads")
        logger.info(f"[{step}/{total_steps}] Created initial set of rules")
        step += 1
        # Step 3: Test the Rules
        aggregation_tracker = {
            "rules_to_optimized": [], # created rules that are primed for aggregation
            "corresponding_payloads": [], # associated payloads that corresponds to the rules primed for aggregation
            "optimized_rules": [], # optimized ruleset after aggregation
            "blocked_payloads":[], # payloads that evaded after optimization
            "evaded_payloads":[], # evaded payloads
        }
        with console.status("Testing newly created WAF rule(s)..."):
            for payload in rules_tracker.keys():
                if rules_tracker[payload] != None:
                    evaluation_status = evaluate_single_modsecurity_rule_with_payload(config, testing_env, rules_tracker[payload], payload)
                    result = {
                        "rule": rules_tracker[payload],
                        "pass_evaluation":  evaluation_status
                    }
                    rules_tracker[payload] = result
                    if evaluation_status:
                        aggregation_tracker["rules_to_optimized"].append(rules_tracker[payload]["rule"])
                        aggregation_tracker["corresponding_payloads"].append(payload)
                    else:
                        # creation of WAF rule did not succeed
                        aggregation_tracker["evaded_payloads"].append(payload)
                else:
                    # cannot create corresponding WAF rule
                    aggregation_tracker["evaded_payloads"].append(payload)
        logger.info(f"[{step}/{total_steps}] Tested {num_of_rules} rules, passed={len(aggregation_tracker["rules_to_optimized"])}")
        step += 1
        # Step 4: Merge the Rules
        with console.status("Aggregating waf rule(s)..."):
            if len(aggregation_tracker["rules_to_optimized"]) >= 2:
                aggregation_tracker["optimized_rules"] = aggregate_modsecurity_rules(config.llm_agent, aggregation_tracker["rules_to_optimized"], config.traffic_payloads)
                logger.info(f"[{step}/{total_steps}] Aggregated {len(aggregation_tracker["optimized_rules"])} from {len(aggregation_tracker["rules_to_optimized"])} WAF rules")
            else:
                logger.info(f"[{step}/{total_steps}] Not enough rules to aggregate, skipping step")
        step += 1
        # Step 5: Test Aggregated Rules
        with console.status("Testing aggregated waf rule(s)..."):
            if len(aggregation_tracker["optimized_rules"]) > 0:
                updated_rules = []
                blocked_payloads_set = set()
                for aggregated_rule in aggregation_tracker["optimized_rules"]:
                    # test each individual rule and make sure it is working
                    blocked_payloads, evaded_payloads = evaluate_single_modsecurity_rule_with_multiple_payloads(config, testing_env, aggregated_rule, aggregation_tracker["corresponding_payloads"])
                    if len(blocked_payloads) > 0:
                        updated_rules.append(aggregated_rule)
                        blocked_payloads_set.update(blocked_payloads)
                aggregation_tracker["optimized_rules"] = updated_rules # remove the rules that do not work
                aggregation_tracker["blocked_payloads"] = list(blocked_payloads_set)
            else:
                logger.info(f"[{step}/{total_steps}] No newly created rules that were aggregated, skipping step")
        step += 1
        # Step 6: Patch Rules
        aggregated_ruleset = aggregation_tracker["optimized_rules"]
        # Payloads that are not caught by the aggregated rules
        remaining_payloads = list((set(aggregation_tracker["corresponding_payloads"]) - set(aggregation_tracker["blocked_payloads"])))
        for remaining_payload in remaining_payloads:
            if rules_tracker[remaining_payload] != None:
                aggregated_ruleset.append(rules_tracker[remaining_payload]["rule"])
                aggregation_tracker["blocked_payloads"].append(remaining_payload)
        aggregation_tracker["optimized_rules"] = aggregated_ruleset
        logger.info(f"[{step}/{total_steps}] Created a total of {len(aggregated_ruleset)} WAF rules, blocking a total of {len(aggregation_tracker["rules_to_optimized"])} payloads from the original {len(config.attack_payloads)} payloads")
        step += 1
        # Step 7: Teardown Testing Enviornment
        with console.status("Decommissioning testing environment"):
            testing_env.teardown()
            time.sleep(1)
        logger.info(f"[{step}/{total_steps}] Decommissioned testing environment")

        # # Write evaded payloads to file if any
        if len(aggregation_tracker["evaded_payloads"]) > 0 and config.output_evaded_path:
            write_results_to_file(
                config.output_evaded_path, 
                aggregation_tracker["evaded_payloads"]
            )
        if len(aggregation_tracker["optimized_rules"]) > 0 and config.output_rules_path:
            write_results_to_file(
                config.output_rules_path, 
                aggregation_tracker["optimized_rules"]
            )

    except Exception as e:
        logger.debug(traceback.format_exc())
        logger.error(f"Fatal Error - will proceed to exit: {e}")
        logger.error(f"Stack trace: {sys.exc_info()[2]}")
        # Ensure environment is torn down in case of error
        try:
            testing_env.teardown()
        except Exception as e:
            logger.exception(f"Failed to teardown testing environment: {e}")
            logger.error("failing quietly to end command")
