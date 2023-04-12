from __future__ import annotations
from enum import Enum
from typing import Any, Optional, Dict, List

from pydantic import BaseModel


class JobCommand(str, Enum):
    sacct = "sacct"
    squeue = "squeue"


class JobStateResponse(BaseModel):
    status: Optional[str] = None
    output: Optional[List[Dict]] = None
    error: Optional[Any] = None


class JobState(str, Enum):
    """
    JobStates
    """

    BOOT_FAIL = "BOOT_FAIL"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    CONFIGURING = "CONFIGURING"
    COMPLETING = "COMPLETING"
    DEADLINE = "DEADLINE"
    FAILED = "FAILED"
    NODE_FAIL = "NODE_FAIL"
    OUT_OF_MEMORY = "OUT_OF_MEMORY"
    PENDING = "PENDING"
    PREEMPTED = "PREEMPTED"
    RUNNING = "RUNNING"
    RESV_DEL_HOLD = "RESV_DEL_HOLD"
    REQUEUE_FED = "REQUEUE_FED"
    REQUEUE_HOLD = "REQUEUE_HOLD"
    REQUEUED = "REQUEUED"
    RESIZING = "RESIZING"
    REVOKED = "REVOKED"
    SIGNALING = "SIGNALING"
    SPECIAL_EXIT = "SPECIAL_EXIT"
    STAGE_OUT = "STAGE_OUT"
    STOPPED = "STOPPED"
    SUSPENDED = "SUSPENDED"
    TIMEOUT = "TIMEOUT"


TERMINAL_STATES = [
    JobState.CANCELLED,
    JobState.COMPLETED,
    JobState.PREEMPTED,
    JobState.OUT_OF_MEMORY,
    JobState.FAILED,
    JobState.TIMEOUT,
]
