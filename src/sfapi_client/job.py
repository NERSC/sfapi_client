from __future__ import annotations
import asyncio
from enum import Enum
from typing import Any, Optional, Dict

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
    machine: Optional[str] = None
    account: Optional[str] = None
    tres_per_node: Optional[str] = None
    min_cpus: Optional[str] = None
    min_tmp_disk: Optional[str] = None
    end_time: Optional[str] = None
    features: Optional[str] = None
    group: Optional[str] = None
    over_subscribe: Optional[str] = None
    jobid: Optional[str] = None
    name: Optional[str] = None
    comment: Optional[str] = None
    time_limit: Optional[str] = None
    min_memory: Optional[str] = None
    req_nodes: Optional[str] = None
    command: Optional[str] = None
    priority: Optional[str] = None
    qos: Optional[str] = None
    reason: Optional[str] = None
    st: Optional[str] = None
    user: Optional[str] = None
    reservation: Optional[str] = None
    wckey: Optional[str] = None
    exc_nodes: Optional[str] = None
    nice: Optional[str] = None
    s_c_t: Optional[str] = Field(None, alias="s:c:t")
    exec_host: Optional[str] = None
    cpus: Optional[str] = None
    nodes: Optional[str] = None
    dependency: Optional[str] = None
    array_job_id: Optional[str] = None
    sockets_per_node: Optional[str] = None
    cores_per_socket: Optional[str] = None
    threads_per_core: Optional[str] = None
    array_task_id: Optional[str] = None
    time_left: Optional[str] = None
    time: Optional[str] = None
    nodelist: Optional[str] = None
    contiguous: Optional[str] = None
    partition: Optional[str] = None
    nodelist_reason_: Optional[str] = Field(None, alias="nodelist(reason)")
    start_time: Optional[str] = None
    state: Optional[JobState] = None
    uid: Optional[str] = None
    submit_time: Optional[str] = None
    licenses: Optional[str] = None
    core_spec: Optional[str] = None
    schednodes: Optional[str] = None
    work_dir: Optional[str] = None

    @validator("state", pre=True)
    def state_validate(cls, v):
        # sacct return a state of the form "CANCELLED by XXXX" for the
        # cancelled state, coerce into value that will match a state
        # modeled by the enum
        if v.startswith("CANCELLED by"):
            return "CANCELLED"

        return v

    async def update(self):
        job_status = await self.compute.client._fetch_job_status(self.jobid)
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
            await asyncio.sleep(10)

        return self

    def __await__(self):
        return self._wait_until_complete().__await__()

    async def complete(self):
        await self

    async def cancel(self, wait=False):
        # We have wait for a jobid before we can cancel
        while self.jobid is None:
            await asyncio.sleep()

        await self.compute.client.delete(
            f"compute/jobs/{self.compute.name}/{self.jobid}"
        )

        if wait:
            while self.state != JobState.CANCELLED:
                await self.update()
                await asyncio.sleep(10)
