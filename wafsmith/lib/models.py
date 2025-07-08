import enum
from pydantic import BaseModel

class LogClassificationType(enum.Enum):
    COMMAND_INJECTION = "command-injection"
    FILE_INCLUSION = "file-inclusion"
    SQL_INJECTION = "sqli"
    CROSS_SITE_SCRIPTING = "xss"
    DIRECTORY_TRAVERSAL = "directory-traversal"
    RECON = "recon"
    NON_MALICIOUS = "non-malicious"
    UNKNOWN = "unknown"

class Classification(BaseModel):
    classification_type: LogClassificationType = LogClassificationType.UNKNOWN
    extracted_payload: str
    reason: str