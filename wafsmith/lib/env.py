import subprocess
import logging
from typing import List, Tuple
from pydantic import BaseModel

logger = logging.getLogger("env")


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
