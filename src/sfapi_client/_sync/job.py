from __future__ import annotations
from enum import Enum
import sys
import math
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, ClassVar
from .common import _SLEEP, SfApiError
from .._models.job_status_response_sacct import OutputItem as JobSacctBase
from .._models.job_status_response_squeue import OutputItem as JobSqueueBase
from .._models import AppRoutersComputeModelsStatus as JobResponseStatus

from pydantic import BaseModel, Field, validator


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


def _fetch_raw_state(
    compute: "Compute",
    jobid: Optional[int] = None,
    user: Optional[str] = None,
    partition: Optional[str] = None,
    sacct: Optional[bool] = False,
):
    params = {"sacct": sacct}

    job_url = f"compute/jobs/{compute.name}"

    if jobid is not None:
        job_url = f"{job_url}/{jobid}"
    elif user is not None:
        params["kwargs"] = f"user={user}"
    elif partition is not None:
        params["kwargs"] = f"partition={partition}"

    r = compute.client.get(job_url, params)

    json_response = r.json()
    job_state_response = JobStateResponse.parse_obj(json_response)

    if job_state_response == JobResponseStatus.ERROR:
        error = json_response.error
        raise SfApiError(error)

    return job_state_response.output


def _fetch_jobs(
    job_type: Union["JobSacct", "JobSqueue"],
    compute: "Compute",
    jobid: Optional[int] = None,
    user: Optional[str] = None,
    partition: Optional[str] = None,
):
    job_states = _fetch_raw_state(
        compute, jobid, user, partition, job_type._command == JobCommand.sacct
    )

    jobs = [job_type.parse_obj(state) for state in job_states]

    for job in jobs:
        job.compute = compute

    return jobs


class Job(BaseModel, ABC):
    """
    Models a job submitted to run on a compute resource.
    """

    compute: Optional["Compute"] = None
    state: Optional[JobState]
    jobid: Optional[str]

    @validator("state", pre=True, check_fields=False)
    def state_validate(cls, v):
        # sacct return a state of the form "CANCELLED by XXXX" for the
        # cancelled state, coerce into value that will match a state
        # modeled by the enum
        if v.startswith("CANCELLED by"):
            return "CANCELLED"

        return v

    def update(self):
        """
        Update the state of the job by fetching the state from the compute resource.
        """
        job_state = self._fetch_state()
        self._update(job_state)

    def _update(self, new_job_state: Any) -> Job:
        for k in new_job_state.__fields_set__:
            v = getattr(new_job_state, k)
            setattr(self, k, v)

        return self

    def _wait_until(self, states: List[JobState], timeout: int = sys.maxsize):
        max_iteration = math.ceil(timeout / 10)
        iteration = 0

        while self.state not in states:
            self.update()
            _SLEEP(10)

            if iteration == max_iteration:
                raise TimeoutError()

            iteration += 1

        return self.state

    def _wait_until_complete(self, timeout: int = sys.maxsize):
        return self._wait_until(TERMINAL_STATES, timeout)

    def __await__(self):
        return self._wait_until_complete().__await__()

    def complete(self, timeout: int = sys.maxsize):
        """
        Wait for a job to move into a terminal state.

        :param timeout: The maximum time to wait in seconds, the actually wait time will be in
        10 second increments.
        :type timeout: int
        :raises: TimeoutError
        """
        return self._wait_until_complete(timeout)

    def running(self, timeout: int = sys.maxsize):
        """
        Wait for a job to move into running state.

        :param timeout: The maximum time to wait in seconds, the actually wait time will be in
        10 second increments.
        :type timeout: int
        :raises: TimeoutError
        """
        state = self._wait_until([JobState.RUNNING] + TERMINAL_STATES, timeout)
        if state != JobState.RUNNING:
            raise SfApiError(
                f"Job never entered the running state, end state was: {state}"
            )

        return state

    def cancel(self, wait=False):
        """
        Cancel a running job

        :param wait: True, to wait for job be to cancel, otherwise returns when cancellation
        has been submitted.
        :type wait: bool


        """
        # We have wait for a jobid before we can cancel
        while self.jobid is None:
            _SLEEP()

        self.compute.client.delete(
            f"compute/jobs/{self.compute.name}/{self.jobid}"
        )

        if wait:
            while self.state != JobState.CANCELLED:
                self.update()
                _SLEEP(10)

    def dict(self, *args, **kwargs) -> Dict:
        if "exclude" not in kwargs:
            kwargs["exclude"] = {"compute"}
        return super().dict(*args, **kwargs)

    @abstractmethod
    def _fetch_state(self):
        pass


class JobSacct(Job, JobSacctBase):
    _command: ClassVar[JobCommand] = JobCommand.sacct

    def _fetch_state(self):
        jobs = self._fetch_jobs(jobid=self.jobid)
        if len(jobs) != 1:
            raise SfApiError(f"Job not found: ${self.jobid}")

        return jobs[0]

    @classmethod
    def _fetch_jobs(
        cls,
        compute: "Compute",
        jobid: Optional[int] = None,
        user: Optional[str] = None,
        partition: Optional[str] = None,
    ):
        return _fetch_jobs(cls, compute, jobid, user, partition)


class JobSqueue(Job, JobSqueueBase):
    _command: ClassVar[JobCommand] = JobCommand.squeue

    def _fetch_state(self):
        jobs = self._fetch_jobs(self.compute, jobid=self.jobid)
        # If the job state comes back empty the job is probably no longer in
        # the queue, so we use sacct to get the final state.
        if len(jobs) == 0:
            jobs = JobSacct._fetch_jobs(self.compute, jobid=self.jobid)
            if len(jobs) != 1:
                raise SfApiError(f"Job not found: ${self.jobid}")

            # We create a new squeue job instance and set the state on it,
            # the update method will then use this to update just the job
            # state field.
            job = JobSqueue()
            job.state = jobs[0].state

            return job

        return jobs[0]

    @classmethod
    def _fetch_jobs(
        cls,
        compute: "Compute",
        jobid: Optional[int] = None,
        user: Optional[str] = None,
        partition: Optional[str] = None,
    ):
        return _fetch_jobs(cls, compute, jobid, user, partition)
