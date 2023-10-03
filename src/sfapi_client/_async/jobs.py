from __future__ import annotations
import sys
import math
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, ClassVar, Union
from .._utils import _ASYNC_SLEEP
from ..exceptions import SfApiError
from .._models.job_status_response_sacct import OutputItem as JobSacctBase
from .._models.job_status_response_squeue import OutputItem as JobSqueueBase
from .._models import AppRoutersComputeModelsStatus as JobResponseStatus

from pydantic import BaseModel, field_validator

from .._jobs import JobCommand
from .._jobs import JobStateResponse
from .._jobs import JobState
from .._jobs import TERMINAL_STATES


async def _fetch_raw_state(
    compute: "AsyncCompute",  # noqa: F821
    jobids: Optional[List[int]] = None,
    user: Optional[str] = None,
    partition: Optional[str] = None,
    sacct: Optional[bool] = False,
):
    params = {"sacct": sacct}

    job_url = f"compute/jobs/{compute.name}"

    if jobids is not None:
        kwargs = params.setdefault("kwargs", [])
        jobid_value = ",".join([str(j) for j in jobids])
        kwargs.append(f"jobid={jobid_value}")

    if user is not None:
        kwargs = params.setdefault("kwargs", [])
        kwargs.append(f"user={user}")

    if partition is not None:
        kwargs = params.setdefault("kwargs", [])
        kwargs.append(f"partition={partition}")

    r = await compute.client.get(job_url, params)

    json_response = r.json()
    job_state_response = JobStateResponse.model_validate(json_response)

    if job_state_response == JobResponseStatus.ERROR:
        error = json_response.error
        raise SfApiError(error)

    return job_state_response.output


async def _fetch_jobs(
    job_type: Union["AsyncJobSacct", "AsyncJobSqueue"],
    compute: "AsyncCompute",  # noqa: F821
    jobids: Optional[List[int]] = None,
    user: Optional[str] = None,
    partition: Optional[str] = None,
):
    job_states = await _fetch_raw_state(
        compute, jobids, user, partition, job_type._command == JobCommand.sacct
    )

    jobs = [
        job_type.model_validate(dict(state, compute=compute)) for state in job_states
    ]

    return jobs


class AsyncJob(BaseModel, ABC):
    """
    Models a job submitted to run on a compute resource.
    """

    compute: Optional["AsyncCompute"] = None  # noqa: F821
    state: Optional[JobState] = None
    jobid: Optional[str] = None

    @field_validator("state", mode="before", check_fields=False)
    def state_validate(cls, v):
        # sacct return a state of the form "CANCELLED by XXXX" for the
        # cancelled state, coerce into value that will match a state
        # modeled by the enum
        if v.startswith("CANCELLED by"):
            return "CANCELLED"

        return v

    async def update(self):
        """
        Update the state of the job by fetching the state from the compute resource.
        """
        job_state = await self._fetch_state()
        self._update(job_state)

    def _update(self, new_job_state: Any) -> Job:  # noqa: F821
        for k in new_job_state.model_fields_set:
            v = getattr(new_job_state, k)
            setattr(self, k, v)

        return self

    async def _wait_until(self, states: List[JobState], timeout: int = sys.maxsize):
        max_iteration = math.ceil(timeout / self.compute.client._wait_interval)
        iteration = 0

        while self.state not in states:
            await self.update()
            await _ASYNC_SLEEP(self.compute.client._wait_interval)

            if iteration == max_iteration:
                raise TimeoutError()

            iteration += 1

        return self.state

    async def _wait_until_complete(self, timeout: int = sys.maxsize):
        return await self._wait_until(TERMINAL_STATES, timeout)

    def __await__(self):
        return self._wait_until_complete().__await__()

    async def complete(self, timeout: int = sys.maxsize):
        """
        Wait for a job to move into a terminal state.

        :param timeout: The maximum time to wait in seconds, the actually
        wait time will be in 10 second increments.
        :raises TimeoutError: if timeout is reached
        """
        return await self._wait_until_complete(timeout)

    async def running(self, timeout: int = sys.maxsize):
        """
        Wait for a job to move into running state.

        :param timeout: The maximum time to wait in seconds, the actually wait
        time will be in 10 second increments.
        :raises TimeoutError: if timeout if reached
        """
        state = await self._wait_until([JobState.RUNNING] + TERMINAL_STATES, timeout)
        if state != JobState.RUNNING:
            raise SfApiError(
                f"Job never entered the running state, end state was: {state}"
            )

        return state

    async def cancel(self, wait=False):
        """
        Cancel a running job

        :param wait: True, to wait for job be to cancel, otherwise returns when
        cancellation
        has been submitted.
        :type wait: bool


        """
        # We have wait for a jobid before we can cancel
        while self.jobid is None:
            await _ASYNC_SLEEP()

        await self.compute.client.delete(
            f"compute/jobs/{self.compute.name}/{self.jobid}"
        )

        if wait:
            while self.state != JobState.CANCELLED:
                await self.update()
                await _ASYNC_SLEEP(self.compute.client._wait_interval)

    def dict(self, *args, **kwargs) -> Dict:
        if "exclude" not in kwargs:
            kwargs["exclude"] = {"compute"}
        return super().dict(*args, **kwargs)

    @abstractmethod
    async def _fetch_state(self):
        pass


class AsyncJobSacct(AsyncJob, JobSacctBase):
    _command: ClassVar[JobCommand] = JobCommand.sacct

    async def _fetch_state(self):
        jobs = await self.compute._monitor.fetch_jobs(
            job_type=self.__class__, jobids=[self.jobid]
        )
        if len(jobs) != 1:
            raise SfApiError(f"Job not found: ${self.jobid}")

        return jobs[0]

    @classmethod
    async def _fetch_jobs(
        cls,
        compute: "AsyncCompute",  # noqa: F821
        jobids: Optional[List[int]] = None,
        user: Optional[str] = None,
        partition: Optional[str] = None,
    ):
        return await _fetch_jobs(cls, compute, jobids, user, partition)


class AsyncJobSqueue(AsyncJob, JobSqueueBase):
    """
    Models a job running on a compute resource, the information is
    fetched using `squeue`.
    """

    _command: ClassVar[JobCommand] = JobCommand.squeue

    async def _fetch_state(self):
        jobs = await self.compute._monitor.fetch_jobs(
            job_type=self.__class__, jobids=[self.jobid]
        )
        # If the job state comes back empty the job is probably no longer in
        # the queue, so we use sacct to get the final state.
        if len(jobs) == 0:
            jobs = await self.compute._monitor.fetch_jobs(
                job_type=AsyncJobSacct, jobids=[self.jobid]
            )
            if len(jobs) != 1:
                raise SfApiError(f"Job not found: {self.jobid}")

            # We create a new squeue job instance and set the state on it,
            # the update method will then use this to update just the job
            # state field.
            job = AsyncJobSqueue()
            job.state = jobs[0].state

            return job

        return jobs[0]

    @classmethod
    async def _fetch_jobs(
        cls,
        compute: "AsyncCompute",  # noqa: F821
        jobids: Optional[List[int]] = None,
        user: Optional[str] = None,
        partition: Optional[str] = None,
    ):
        return await _fetch_jobs(cls, compute, jobids, user, partition)
