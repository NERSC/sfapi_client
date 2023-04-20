from typing import Optional
from enum import Enum
from pydantic import BaseModel


class SubmitJobResponseStatus(Enum):
    OK = "OK"
    ERROR = "ERROR"


class SubmitJobResponse(BaseModel):
    task_id: str
    status: SubmitJobResponseStatus
    error: Optional[str]


class CommandResult(BaseModel):
    status: str
    output: Optional[str]
    error: Optional[str]
