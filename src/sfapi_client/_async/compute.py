import asyncio
from typing import List, Optional
import json
from enum import Enum
from pydantic import BaseModel

from .common import SfApiError, _ASYNC_SLEEP
from .job import JobSacct, JobSqueue, Job, JobCommand
from .._models import (
    AppRoutersStatusModelsStatus as ComputeBase,
    AppRoutersComputeModelsStatus as JobStatus,
    PublicHost as Machines,
    Task,
)

from .._models.job_status_response_sacct import JobStatusResponseSacct
from .._models.job_status_response_squeue import JobStatusResponseSqueue


class SubmitJobResponseStatus(Enum):
    OK = "OK"
    ERROR = "ERROR"


class SubmitJobResponse(BaseModel):
    task_id: str
    status: SubmitJobResponseStatus
    error: Optional[str]


class Compute(ComputeBase):
    client: Optional["AsyncClient"]

    async def submit_job(self, batch_submit_filepath: str) -> "Job":
        data = {"job": batch_submit_filepath, "isPath": True}

        r = await self.client.post(f"compute/jobs/{self.name}", data)
        r.raise_for_status()

        json_response = r.json()
        job_response = SubmitJobResponse.parse_obj(json_response)

        if job_response.status == SubmitJobResponseStatus.ERROR:
            raise SfApiError(job_response.error)

        task_id = job_response.task_id

        # We now need to poll waiting for the task to complete!
        while True:
            r = await self.client.get(f"tasks/{task_id}")
            r.raise_for_status()

            json_response = r.json()
            task = Task.parse_obj(json_response)

            if task.status.lower() in ["error", "failed"]:
                raise SfApiError(task.result)

            if task.result is None:
                await _ASYNC_SLEEP(1)
                continue

            result = json.loads(task.result)
            if result.get("status") == "error":
                raise SfApiError(result["error"])

            jobid = result.get("jobid")
            if jobid is None:
                raise SfApiError(f"Unable to extract jobid if for task: {task_id}")

            job = Job(jobid=jobid)
            job.compute = self

            return job

    async def _fetch_job_status(
        self,
        jobid: Optional[int] = None,
        user: Optional[str] = None,
        partition: Optional[str] = None,
        command: Optional[JobCommand] = None,
    ):
        # Default from api
        params = {"sacct": False}

        # Could be changed to `match case` but that limits to 3.10+
        if command == JobCommand.sacct:
            params = {"sacct": True}
            JobStatusResponse = JobStatusResponseSacct
        elif command == JobCommand.squeue:
            params = {"sacct": False}
            JobStatusResponse = JobStatusResponseSqueue

        job_url = f"compute/jobs/{self.name}"

        if jobid is not None:
            job_url = f"{job_url}/{jobid}"
        elif user is not None:
            params["kwargs"] = f"user={user}"
        elif partition is not None:
            params["kwargs"] = f"partition={partition}"

        r = await self.client.get(job_url, params)

        json_response = r.json()
        job_status = JobStatusResponse.parse_obj(json_response)

        if job_status.status == JobStatus.ERROR:
            error = job_status.error
            raise SfApiError(error)

        return job_status.output

    async def job(
        self, jobid: int, command: Optional[JobCommand] = JobCommand.sacct
    ) -> "Job":
        job_status = await self._fetch_job_status(jobid=jobid, command=command)
        # Get different job depending on query
        Job = JobSacct if (command == JobCommand.sacct) else JobSqueue
        job = Job.parse_obj(job_status[0])
        job.compute = self

        return job

    async def jobs(
        self,
        user: Optional[str] = None,
        partition: Optional[str] = None,
        command: Optional[JobCommand] = JobCommand.squeue,
    ) -> List["Job"]:
        job_status = await self._fetch_job_status(
            user=user, partition=partition, command=command
        )
        # Get different job depending on command
        Job = JobSacct if (command == JobCommand.sacct) else JobSqueue

        jobs = []
        # Fills jobs list with a Job object
        # parsed from json into pydantic model object
        for _job in job_status:
            jobs.append(Job.parse_obj(_job))
            jobs[-1].compute = self

        return jobs
