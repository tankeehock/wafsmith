import os
import logging
from typing import List, Optional
from pydantic import BaseModel
from wafsmith.lib.llm import LLMAgent

logger = logging.getLogger("config")


class EvaluateConfig(BaseModel):
    setup_dir: str = "./infra/"
    attack_payloads: List[str] = []
    attack_payloads_dir: str = "./payloads/"

    logs_directory: Optional[str] = None
    logs: Optional[List[str]] = None

    output_evaded_path: Optional[str] = None
    output_rules_path: Optional[str] = None
    output_payloads_path: Optional[str] = None

    traffic_payloads_dir: Optional[str] = None
    traffic_payloads: List[str] = []

    position: str = "url_parameters"
    method: str = "GET"
    threads: int = 5
    host: str = "http://localhost/"

    llm_agent: LLMAgent = None
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1" # defaults to OpenAI endpoint
    model: str = "gpt-4o" # defaults to OpenAI's GPT-4o model

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

    def validateCreateConfig(self) -> bool:
        ok = True
        if self.validate():
            # perform validation for LLM API
            # TODO
            if not os.path.exists(os.path.dirname(self.output_rules_path)):
                logger.info("creating directory for modsecurity rules")
                os.makedirs(os.path.dirname(self.output_rules_path))
            ok = True
        else:
            ok = False
        return ok

    def validateExtractConfig(self) -> bool:
        ok = True
        if not os.path.exists(os.path.dirname(self.output_payloads_path)):
            logger.info("creating directory for extracted payloads")
            os.makedirs(os.path.dirname(self.output_rules_path))
            ok = True
        
        if not os.path.exists(self.logs_directory):
                logger.error(
                    "logs directory not defined, skipping payload extraction."
                )
                ok = False

        # perform validation for LLM API
        # TODO

        return ok

    def load(self):
        self.attack_payloads = read_all_file_content_in_directory(
            self.attack_payloads_dir
        )
        self.traffic_payloads = read_all_file_content_in_directory(
            self.traffic_payloads_dir
        )

    def loadLogsDirectory(self):
        self.logs = read_all_file_content_in_directory(self.logs_directory)

    def loadLLMService(self):
        self.llm_agent = LLMAgent(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model
        )
        self.llm_agent.setup()

def read_all_file_content_in_directory(directory_path: str) -> List[str]:
    all_content = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            all_content.extend(read_file(file_path))
            # with open(file_path, "r") as f:
            #     all_content.extend([line.strip() for line in f.readlines()])
    return all_content

def read_file(file_path: str) -> List[str]:
    with open(file_path, "r") as f:
        return [line.strip() for line in f.readlines()]
