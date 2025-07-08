import subprocess, logging, os, enum
from typing import List, Tuple
from pydantic import BaseModel
from wafsmith.utils.helper import Utility
import time

logger = logging.getLogger("env")

class DOCKER_SERVICE_META(enum.Enum):
    WEB = {
        "name":"web-app",
        "id": "root"
    }
    WAF = {
        "name": "crs-nginx",
        "id": "nginx"
    }

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

    def teardown(self):
        p = subprocess.Popen(
            ["docker", "compose", "-f", self.compose_file, "down"],
            cwd=self.base_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        p.wait()
    
    def restart_waf_container(self) -> bool:
        p = subprocess.Popen(
            ["docker","compose","restart",DOCKER_SERVICE_META.WAF.value["name"]],
            cwd=self.base_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        p.wait()
        time.sleep(1) # need to wait for the docker finish execution
        return self.checkContainerHealthByID(DOCKER_SERVICE_META.WAF)

    def exec(self, cmd: List[str]) -> Tuple[int, bytes, bytes]:
        """
        exec returns the statuscode, stdout, stderr for a given command
        """
        p = subprocess.Popen(
            cmd, cwd=self.base_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return p.wait(), p.stdout.read(), p.stderr.read()
    
    def deployNewModSecurityRule(self, modsecurity_rule) -> (bool, str):
        """Deploys the new ModSecurity rule

        Args:
            modsecurity_rule: ModSecurity rule

        Returns:
            Boolean of the deployment status
        """
        modsecurity_rule_path = os.path.join(self.base_dir, "rules", Utility.generate_unique_file_name("wafsmith",modsecurity_rule))
        with open(modsecurity_rule_path, "w") as file:
            file.write(modsecurity_rule)
        logger.debug(f"created new modsecurity rule filepath={modsecurity_rule_path}")
        waf_container_health = self.restart_waf_container()
        if not waf_container_health:
            # there are errors deploying the container
            # do a clean up
            self.deleteModSecurityRule(modsecurity_rule_path)
            self.restart_waf_container()
            return (False, modsecurity_rule_path)
        else:
            return (True, modsecurity_rule_path)
        
    def deleteModSecurityRule(self, file_path) -> bool:
        try:
            os.remove(file_path)
            logger.debug(f"deleted modsecurity rule filepath={file_path}")
            return True
        except Exception as e:
            return False


    def checkContainerHealthByID(self, service_name: DOCKER_SERVICE_META) -> bool:
        status, stdout, stderr = self.exec(["docker","compose", "exec",service_name.value["name"],"id"])
        if status == 0 and service_name.value["id"] in stdout.decode("utf-8"):
            # if the service responds with the correct user id,
            # it shows that the container is running
            # health check can be improved
            return True
        else:
            return False

    """
    export async function RedeployCRSContainer(path) {
    // TODO check if container can be deployed
    let command = `cd ${path} && docker compose restart crs-nginx`;
        await ExecuteCommand(command);
    }

    export async function DeployTestingEnviornment(path) {
        let command = `cd ${path} && docker compose up -d`;
        await ExecuteCommand(command);
    }

    export async function TeardownTestingEnviornment(path) {
        let command = `cd ${path} && docker compose down`;
        await ExecuteCommand(command);
    }
    """