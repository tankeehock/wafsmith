import os
import sys
import json
import time
import xml.etree.ElementTree as ET
import logging
import subprocess
import enum
import requests
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from wafsmith.lib.console import console

from typing import List, Dict, Any, Optional, Tuple, Callable
from pydantic import BaseModel

logger = logging.getLogger("evaluate")


class EvaluateConfig(BaseModel):
    setup_dir: str = "./infra/"
    attack_payloads: List[str] = []
    attack_payloads_dir: str = "./payloads/"

    output_evaded_path: Optional[str] = None
    traffic_payloads_dir: Optional[str] = None
    traffic_payloads: List[str] = []

    position: str = "url_parameters"
    method: str = "GET"
    threads: int = 5
    host: str = "http://localhost:3000"

    def validate(self) -> bool:
        ok = True

        if not os.path.exists(self.traffic_payloads_dir):
            logger.info(
                "traffic payloads directory not defined, skipping business traffic simulation."
            )

        if not os.path.exists(self.attack_payloads_dir):
            logger.error(
                "attack payloads directory not defined, skipping attack payload simulation."
            )
            ok = False

        if not os.path.exists(os.path.dirname(self.output_evaded_path)):
            logger.info("creating directory for evaded payloads")
            os.makedirs(os.path.dirname(self.output_evaded_path))

        if not os.path.exists(os.path.join(self.setup_dir, "docker-compose.yml")):
            logger.error("failed to find docker-compose file for initializing testing")
            ok = False

        if not os.path.exists(self.attack_payloads_dir):
            logger.error("failed to find payload directory")
            ok = False

        return ok

    def load(self):
        self.attack_payloads = read_all_file_content_in_directory(
            self.attack_payloads_dir
        )
        self.traffic_payloads = read_all_file_content_in_directory(
            self.traffic_payloads_dir
        )


def read_all_file_content_in_directory(directory_path: str) -> List[str]:
    all_content = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, "r") as f:
                all_content.extend([line.strip() for line in f.readlines()])
    return all_content


def run(
    payloads_dir: str,
    evaded_file: str,
    setup_dir: str,
    traffic_path: str,
    position: str,
    method: str,
    threads: int,
    host: str = "http://localhost:3000",
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


class Location(enum.Enum):
    URL_PARAMETERS = 1
    HTTP_HEADER = 2
    HTTP_BODY = 3


class Encoding(enum.Enum):
    FORM_URLENCODED = 1
    JSON = 2
    XML = 3

    def content_type(self) -> str:
        return {
            Encoding.FORM_URLENCODED: "application/x-www-form-urlencoded",
            Encoding.JSON: "application/json",
            Encoding.XML: "application/xml",
        }[self]


class Payload(BaseModel):
    method: str = "GET"
    endpoint: str
    payload: str
    location: Location = Location.URL_PARAMETERS
    encoding: Encoding = Encoding.FORM_URLENCODED

    def __str__(self) -> str:
        return f"{self.method} {self.endpoint} {self.payload}"

    def build_body(self) -> bytes:
        if self.encoding == Encoding.FORM_URLENCODED:
            return self.payload.encode("utf-8")
        if self.encoding == Encoding.JSON:
            return json.dumps({"payload": self.payload}).encode("utf-8")
        if self.encoding == Encoding.XML:
            root = ET.Element("payload")
            root.text = self.payload
            return ET.tostring(root, encoding="utf-8")
        return self.payload

    def send_request(self) -> int:
        params = {}
        headers = {}
        data = None
        if self.location == Location.URL_PARAMETERS:
            params = {"payload": self.payload}
        elif self.location == Location.HTTP_HEADER:
            headers = {"x-payload": self.payload}
        elif self.location == Location.HTTP_BODY:
            data = self.build_body()
            headers["Content-Type"] = self.encoding.content_type()

        try:
            if self.method == "GET":
                response = requests.get(self.endpoint, headers=headers, params=params)
            else:  # POST
                response = requests.post(self.endpoint, headers=headers, data=data)
            return response.status_code
        except Exception as e:
            logger.error(f"Error sending request: {e}")
            return 500  # Return 500 as a default error code


class TestingEnv(BaseModel):
    base_dir: str = "./infra/"
    compose_file: str = "docker-compose.yml"

    def setup(self):
        p = subprocess.Popen(
            ["docker", "compose", "-f", self.compose_file, "up", "-d"],
            cwd=self.base_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        p.wait()
        logger.info(p.stdout.read())
        logger.info(p.stderr.read())

    def teardown(self):
        p = subprocess.Popen(
            ["docker", "compose", "-f", self.compose_file, "down"],
            cwd=self.base_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        p.wait()

    def exec(self, cmd: List[str]) -> Tuple[int, bytes, bytes]:
        """
        exec returns the statuscode, stdout, stderr for a given command
        """
        p = subprocess.Popen(
            cmd, cwd=self.base_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return p.wait(), p.stdout.read(), p.stderr.read()


def process_payload(args: Tuple[str, str, str, Location, str]) -> Tuple[str, int]:
    """Process a single payload and return the result.
    
    Args:
        args: Tuple containing (payload_str, method, endpoint, location, message)
        
    Returns:
        Tuple of (payload_str, status_code)
    """
    payload_str, method, endpoint, location, message = args
    try:
        payload = Payload(
            method=method,
            endpoint=endpoint,
            payload=payload_str,
            location=location,
        )
        status_code = payload.send_request()
    except Exception as e:
        logger.error(f"Error testing {message}: {e}")
        status_code = 500  # Default error code
    
    return payload_str, status_code


def process_payloads_in_parallel(
    payloads: List[str],
    method: str,
    endpoint: str,
    location: Location,
    threads: int,
    message: str = "payload"
) -> Dict[int, List[str]]:
    """Process multiple payloads in parallel using threading.
    
    Args:
        payloads: List of payload strings to process
        method: HTTP method to use
        endpoint: Endpoint URL
        location: Location enum value
        threads: Number of threads to use
        message: Message to use in logs
        
    Returns:
        Dictionary mapping status codes to lists of payloads
    """
    results: Dict[int, List[str]] = {}
    
    # Prepare arguments for parallel processing
    args = [(p, method, endpoint, location, message) for p in payloads]
    
    # Use ThreadPoolExecutor for parallel processing (better for I/O bound tasks)
    max_workers = min(threads, multiprocessing.cpu_count() * 2)  # More threads for I/O bound tasks
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for payload_str, status_code in executor.map(process_payload, args):
            if status_code not in results:
                results[status_code] = []
            results[status_code].append(payload_str)
    
    return results


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


def evaluate(config: EvaluateConfig):
    logger.info("Starting evaluation workflow")
    step = 1
    total_steps = 3

    try:
        # Step 1: Deploy testing environment
        with console.status(f"Deploying testing environment") as status:
            testing_env = TestingEnv(base_dir=config.setup_dir)
            testing_env.setup()
            time.sleep(2)  # Give some time for the environment to start
        logger.info(f"[{step}/{total_steps}] Deployed testing environment")
        step += 1

        # Get location from config
        location: Location = {
            "http_header": Location.HTTP_HEADER,
            "http_body": Location.HTTP_BODY,
        }.get(config.position, Location.URL_PARAMETERS)

        # Step 2: Test attack payloads
        attack_results = {"total": len(config.attack_payloads), "data": {}}
        with console.status(
            f"Testing {len(config.attack_payloads)} attack payloads"
        ) as status:
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
            ) as status:
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
        with console.status("Decommissioning testing environment") as status:
            testing_env.teardown()
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
            write_results_to_file(
                config.output_evaded_path, 
                attack_results["data"].get(200, [])
            )

    except Exception as e:
        logger.error(f"Fatal Error - will proceed to exit: {e}")
        logger.error(f"Stack trace: {sys.exc_info()[2]}")
        # Ensure environment is torn down in case of error
        try:
            testing_env.teardown()
        except:
            pass
