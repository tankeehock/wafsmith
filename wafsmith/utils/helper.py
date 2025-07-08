from typing import Dict, List
import re, random, hashlib
from pydantic import BaseModel
from wafsmith.lib.models import Classification, LogClassificationType
from wafsmith.utils.constants import MIN_ID, MAX_ID
import json, logging
import traceback
logger = logging.getLogger("utility")

class Utility(BaseModel):
    @staticmethod
    def validate_regular_expression(expression: str, payload:str) -> bool:
        try:
            if re.search(expression, payload):
                return True
            else:
                return False
        except:
            return False
    @staticmethod
    def generate_random_modsecurity_id(min=MIN_ID,max=MAX_ID):
        return random.randrange(min, max)
    
    @staticmethod
    def count_created_rules(tracker: Dict[str, str]) -> (int, int):
        payloads = tracker.keys()
        valid_rules = 0
        for payload in payloads:
            if tracker[payload] != None:
                valid_rules += 1
        return (len(payloads), valid_rules)

    @staticmethod
    def generate_SHA256_hash(content: str) -> str:
        hash_object = hashlib.sha256(content.encode('utf-8')) # Encode to bytes
        return hash_object.hexdigest()

    @staticmethod
    def generate_unique_file_name(prefix: str, content: str, suffix: str = ".conf"):
        return prefix + "-" + Utility.generate_SHA256_hash(content) + suffix
    
    @staticmethod
    def convert_raw_log_classifion_output_to_classication_object(json_str: str) -> Classification:
        classification = None
        try:
            # Transform the data
            if "```json" in json_str:
                json_str = Utility.extract_json_payload(json_str)
            transformed_object = json.loads(json_str)
            log_classification_type: LogClassificationType = {
                "command-injection": LogClassificationType.COMMAND_INJECTION,
                "file-inclusion": LogClassificationType.FILE_INCLUSION,
                "sqli": LogClassificationType.SQL_INJECTION,
                "xss": LogClassificationType.CROSS_SITE_SCRIPTING,
                "directory-traversal": LogClassificationType.DIRECTORY_TRAVERSAL,
                "recon": LogClassificationType.RECON,
                "non-malicious": LogClassificationType.NON_MALICIOUS,
            }.get(transformed_object["classification"], LogClassificationType.UNKNOWN)
            classification = Classification(classification_type=log_classification_type, extracted_payload=transformed_object["extracted_payload"], reason=transformed_object["reason"])
        except Exception as e:
            pass
        return classification
    @staticmethod
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
    @staticmethod
    def extract_json_payload(text: str) -> str:
        """
        Extracts the JSON payload from a markdown code block with ```json.
        Args:
            text (str): The input string containing the JSON markdown code block.
        Returns:
            str: The extracted JSON payload as a string, or an empty string if no JSON block found.
        """
        # Regex to match ```json ... ``` block, including multiline content
        pattern = r"```json\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            json_payload = match.group(1)
            # Optionally, strip leading/trailing whitespace
            return json_payload.strip()
        else:
            return ""