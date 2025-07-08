import enum
import json
import xml.etree.ElementTree as ET
import logging
import requests
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple
from pydantic import BaseModel

logger = logging.getLogger("payload")


class PayloadLocation(enum.Enum):
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
    location: PayloadLocation = PayloadLocation.URL_PARAMETERS
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
        if self.location == PayloadLocation.URL_PARAMETERS:
            params = {"payload": self.payload}
        elif self.location == PayloadLocation.HTTP_HEADER:
            headers = {"x-payload": self.payload}
        elif self.location == PayloadLocation.HTTP_BODY:
            data = self.build_body()
            headers["Content-Type"] = self.encoding.content_type()
        logger.debug(f"sending payload endpoint={self.endpoint} method={self.method} headers={headers} payload={self.payload}")
        # proxies = {
        #     'http': 'http://127.0.0.1:8080',
        #     'https': 'http://127.0.0.1:8080'
        # }
        try:
            if self.method == "GET":
                response = requests.get(self.endpoint, headers=headers, params=params, timeout=10, verify=False)
            else:  # POST
                response = requests.post(self.endpoint, headers=headers, data=data, timeout=10, verify=False)
            return response.status_code
        except Exception as e:
            logger.error(f"Error sending request: {e}")
            return 500  # Return 500 as a default error code


def process_payload(args: Tuple[str, str, str, PayloadLocation, str]) -> Tuple[str, int]:
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
    location: PayloadLocation,
    threads: int,
    message: str = "payload",
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
    max_workers = min(
        threads, multiprocessing.cpu_count() * 2
    )  # More threads for I/O bound tasks
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for payload_str, status_code in executor.map(process_payload, args):
            if status_code not in results:
                results[status_code] = []
            results[status_code].append(payload_str)

    return results
