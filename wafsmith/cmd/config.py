import os
import logging
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger("config")


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
