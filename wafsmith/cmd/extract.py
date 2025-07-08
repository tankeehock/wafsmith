import sys
import time
import logging
import traceback
from wafsmith.lib.console import console
from wafsmith.cmd.config import EvaluateConfig
from wafsmith.lib.llm import classify_logs_in_parrallel
from wafsmith.lib.models import LogClassificationType

from wafsmith.utils.helper import Utility

logger = logging.getLogger("extract")

def run(
    logs_directory: str,
    output_payloads_path: str,
    threads: int,
    api_key: str,
    base_url: str, 
    model: str,
):
    logger.info("Validating CLI arguments")

    config = EvaluateConfig(
        output_payloads_path=output_payloads_path,
        logs_directory=logs_directory,
        threads=threads,
        api_key=api_key,
        base_url=base_url,
        model=model
    )

    if not config.validateExtractConfig():
        logger.error("Configuration validation failed.")
        return

    logger.info("Validation complete.")

    try:
        config.loadLogsDirectory()
        config.loadLLMService()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return

    logger.info("Extract Payloads")
    start_time = time.time()

    extract(config)

    end_time = time.time()
    logger.info(f"Extract Payloads: {end_time - start_time:.2f}s")

def extract(config: EvaluateConfig):
    logger.info("Starting extraction workflow")
    step = 1
    total_steps = 2
    try:
        with console.status("Extracting potential payloads from logs directory"):
            classifications = classify_logs_in_parrallel(config.llm_agent,config.logs, config.threads)
            logger.info(f"Successfully performed {len(classifications)} classifications from {len(config.logs)} log entries")
        logger.info(f"[{step}/{total_steps}] Extracted potential payloads from logs directory")
        step += 1
        
        known_malicious_payloads = set()
        for classification in classifications:
            if classification and classification.classification_type != LogClassificationType.NON_MALICIOUS and classification.classification_type != LogClassificationType.UNKNOWN:
                known_malicious_payloads.add(classification.extracted_payload)
        logger.info(f"[{step}/{total_steps}] Found {len(known_malicious_payloads)} malicious payloads from {len(config.logs)} log entries")
        
        # Write payloads to file if any
        if len(known_malicious_payloads) > 0 and config.output_payloads_path:
            Utility.write_results_to_file(
                config.output_payloads_path, 
                list(known_malicious_payloads)
            )

    except Exception as e:
        logger.debug(traceback.format_exc())
        logger.error(f"Fatal Error - will proceed to exit: {e}")
        logger.error(f"Stack trace: {sys.exc_info()[2]}")
        # Ensure environment is torn down in case of error
