import sys
import time
import logging
from wafsmith.lib.console import console
from wafsmith.cmd.config import EvaluateConfig
from wafsmith.lib.payload import Payload, PayloadLocation, process_payload, process_payloads_in_parallel
from wafsmith.lib.env import TestingEnv
from wafsmith.utils.constants import WAF_EXPECTED_STATUS_CODE,DEFAULT_HOST

from typing import List, Dict, Any, Tuple

from wafsmith.utils.helper import Utility

logger = logging.getLogger("evaluate")

def run(
    payloads_dir: str,
    evaded_file: str,
    setup_dir: str,
    traffic_path: str,
    position: str,
    method: str,
    threads: int,
    host: str = DEFAULT_HOST,
):
    logger.info("Validating CLI arguments and preparing testing environment...")

    config = EvaluateConfig(
        setup_dir=setup_dir,
        output_evaded_path=evaded_file,
        attack_payloads_dir=payloads_dir,
        traffic_payloads_dir=traffic_path,
        position=position,
        method=method,
        threads=threads,
        host=host,
    )
    if not config.validate():
        logger.error("Configuration validation failed.")
        return

    logger.info("Validation complete.")

    try:
        config.load()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return

    logger.info("Evaluate WAF Rules")
    start_time = time.time()

    evaluate(config)

    end_time = time.time()
    logger.info(f"Evaluate WAF Rules: {end_time - start_time:.2f}s")


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

def evaluate(config: EvaluateConfig):
    logger.info("Starting evaluation workflow")
    step = 1
    total_steps = 3

    try:
        # Step 1: Deploy testing environment
        with console.status("Deploying testing environment"):
            testing_env = TestingEnv(base_dir=config.setup_dir)
            testing_env.setup()
            time.sleep(2)  # Give some time for the environment to start
        logger.info(f"[{step}/{total_steps}] Deployed testing environment")
        step += 1

        # Get location from config
        location: PayloadLocation = {
            "http_header": PayloadLocation.HTTP_HEADER,
            "http_body": PayloadLocation.HTTP_BODY,
        }.get(config.position, PayloadLocation.URL_PARAMETERS)

        # Step 2: Test attack payloads
        attack_results = {"total": len(config.attack_payloads), "data": {}}
        with console.status(f"Testing {len(config.attack_payloads)} attack payloads"):
            attack_results["data"] = process_payloads_in_parallel(
                config.attack_payloads,
                config.method,
                config.host,
                location,
                config.threads,
                "attack payload"
            )

        logger.info(f"[{step}/{total_steps}] Completed testing of payloads")
        step += 1

        # Step 3: Test business traffic if available
        business_traffic_status = "yet-to-test"
        if config.traffic_payloads and len(config.traffic_payloads) > 0:
            with console.status(
                f"Testing {len(config.traffic_payloads)} business traffic payloads"
            ):
                business_results = {"total": len(config.traffic_payloads), "data": {}}
                business_results["data"] = process_payloads_in_parallel(
                    config.traffic_payloads,
                    config.method,
                    config.host,
                    location,
                    config.threads,
                    "business traffic"
                )
                
                # For business traffic, we expect 200 status code
                _, _, _, all_passed = calculate_results(business_results, 200)
                business_traffic_status = "passed" if all_passed else "failed"

        # Step 4: Teardown testing environment
        with console.status("Decommissioning testing environment"):
            testing_env.teardown()
            time.sleep(1)
        logger.info(f"[{step}/{total_steps}] Decommissioned testing environment")

        # Print results
        if business_traffic_status == "passed":
            logger.info("\nBusiness Traffic Simulation Status: passed")
        elif business_traffic_status == "yet-to-test":
            logger.info("\nBusiness Traffic Simulation Status: yet-to-test")
        else:
            logger.error("\nBusiness Traffic Simulation Status: failed")

        # Calculate and print evaded payloads
        evaded_count, total_count, evaded_percentage, _ = calculate_results(attack_results)

        if evaded_count == total_count:
            logger.error(
                f"Evaded Payload(s): {evaded_count}/{total_count} ({evaded_percentage:.2f}%)"
            )
        elif evaded_count > 0:
            logger.warning(
                f"Evaded Payload(s): {evaded_count}/{total_count} ({evaded_percentage:.2f}%)"
            )
        else:
            logger.info(f"Evaded Payload(s): 0/{total_count} (0.00%)")

        # Write evaded payloads to file if any
        if evaded_count > 0 and config.output_evaded_path:
            Utility.write_results_to_file(
                config.output_evaded_path, 
                attack_results["data"].get(200, [])
            )

    except Exception as e:
        logger.error(f"Fatal Error - will proceed to exit: {e}")
        logger.error(f"Stack trace: {sys.exc_info()[2]}")
        # Ensure environment is torn down in case of error
        try:
            testing_env.teardown()
        except Exception as e:
            logger.exception(f"Failed to teardown testing environment: {e}")
            logger.error("failing quietly to end command")

def evaluate_single_payload(config: EvaluateConfig, payload: str)-> bool: 
    try:
        location: PayloadLocation = {
            "http_header": PayloadLocation.HTTP_HEADER,
            "http_body": PayloadLocation.HTTP_BODY,
        }.get(config.position, PayloadLocation.URL_PARAMETERS)
        args = (payload, config.method, config.host, location,"attack payload")
        _, status_code = process_payload(args)
        business_traffic_status = False
        business_traffic_test_results = {
            "data": {},
            "total": len(config.traffic_payloads)
        }
        if status_code == WAF_EXPECTED_STATUS_CODE and config.traffic_payloads and len(config.traffic_payloads) > 0:
            business_traffic_test_results["data"] = process_payloads_in_parallel(
                config.traffic_payloads,
                config.method,
                config.host,
                location,
                config.threads,
                "business traffic"
            )
                
        _, _, _, all_passed = calculate_results(business_traffic_test_results, 200)
        business_traffic_status = True if all_passed else False
        
        return business_traffic_status and status_code == WAF_EXPECTED_STATUS_CODE

    except Exception as e:
        logger.error(f"Fatal Error - will proceed to exit: {e}")
        logger.error(f"Stack trace: {sys.exc_info()[2]}")
        # Ensure environment is torn down in case of error
    return False

def evaluate_single_modsecurity_rule_with_multiple_payloads(config: EvaluateConfig, testing_env: TestingEnv, mod_security_rule: str, payloads: List[str]) -> (List[str], List[str]):
    blocked_payloads = []
    evaded_payloads = []
    for payload in payloads:
        if evaluate_single_modsecurity_rule_with_payload(config, testing_env, mod_security_rule, payload):
            blocked_payloads.append(payload)
        else:
            evaded_payloads.append(payload)
    return (blocked_payloads, evaded_payloads)

def evaluate_single_modsecurity_rule_with_payload(config: EvaluateConfig, testing_env: TestingEnv, mod_security_rule: str, payload: str) -> bool:
    """Evaluate the single ModSecurity rule against the corresponding payload

    Args:
        mod_security_rule: ModSecurity Rule
        payload: Corresponding payload that the ModSecurity rule is designed to catch

    Returns:
        Boolean status if the payload evades the ModSecurity rule. If the ModSecurity rule is malformed, it returns False
    """
    evaluation_result = False
    rule_creation_status, new_rule_file_path = testing_env.deployNewModSecurityRule(mod_security_rule)
    if rule_creation_status:
        evaluation_result = evaluate_single_payload(config, payload)
        testing_env.deleteModSecurityRule(new_rule_file_path)
        testing_env.restart_waf_container()
    time.sleep(1)
    return evaluation_result

def evaluate_all_modsecurity_rules_with_payloads(payloads: List[str], mod_security_rules: List[str]) -> List[str]:
    """Evaluate the aggregated ModSecurity rules against the corresponding payloads

    Args:
        mod_security_rules: ModSecurity Rules
        payloads: Corresponding payloads

    Returns:
        List of evaded payloads
    """
    pass