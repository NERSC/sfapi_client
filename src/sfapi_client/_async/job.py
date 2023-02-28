from __future__ import annotations
import asyncio
from enum import Enum
import json
from typing import Any, Optional, Dict
from .common import _ASYNC_SLEEP, SfApiError
from .._models.job_status_response_sacct import OutputItem as JobSacctBase
from .._models.job_status_response_squeue import OutputItem as JobSqueueBase

from pydantic import BaseModel, Field, validator


class JobState(str, Enum):
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


class Job(BaseModel):
    compute: Optional["Compute"] = None

    @validator("state", pre=True, check_fields=False)
    def state_validate(cls, v):
        # sacct return a state of the form "CANCELLED by XXXX" for the
        # cancelled state, coerce into value that will match a state
        # modeled by the enum
        if v.startswith("CANCELLED by"):
            return "CANCELLED"

        return v

    async def update(self):
        job_status = await self.compute._fetch_job_status(self.jobid)
        self._update(job_status)

    def _update(self, data: Dict) -> Any:
        new_job_state = Job.parse_obj(data)

        for k in new_job_state.__fields_set__:
            v = getattr(new_job_state, k)
            setattr(self, k, v)

        return self

    async def _wait_until_complete(self):
        while self.state not in TERMINAL_STATES:
            await self.update()
            await _ASYNC_SLEEP(10)

        return self

    def __await__(self):
        return self._wait_until_complete().__await__()

    async def complete(self):
        await self._wait_until_complete()

    async def cancel(self, wait=False):
        # We have wait for a jobid before we can cancel
        while self.jobid is None:
            await _ASYNC_SLEEP()

        await self.compute.client.delete(
            f"compute/jobs/{self.compute.name}/{self.jobid}"
        )

        if wait:
            while self.state != JobState.CANCELLED:
                await self.update()
                await _ASYNC_SLEEP(10)

    def __str__(self) -> str:
        output = self.dict(exclude={"compute"})
        return json.dumps(output)


class JobSacct(Job, JobSacctBase):
    pass


class JobSqueue(Job, JobSqueueBase):
    pass
