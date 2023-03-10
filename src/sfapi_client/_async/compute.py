import asyncio
from typing import List, Optional
import json
from enum import Enum
from pydantic import BaseModel
from pathlib import PurePosixPath

from .common import SfApiError, _ASYNC_SLEEP
from .job import JobSacct, JobSqueue, JobSqueue, JobCommand
from .._models import (
    AppRoutersStatusModelsStatus as ComputeBase,
    AppRoutersComputeModelsStatus as JobStatus,
    PublicHost as Machines,
    Task,
    DirectoryOutput as DirectoryListingResponse,
    AppRoutersUtilsModelsStatus as DirectoryListingResponseStatus,
)
from .path import RemotePath

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

            job = JobSqueue(jobid=jobid)
            job.compute = self

            return job

    async def job(
        self, jobid: int, command: Optional[JobCommand] = JobCommand.sacct
    ) -> "Union[JobSacct, JobSqueue]":
        # Get different job depending on query
        Job = JobSacct if (command == JobCommand.sacct) else JobSqueue
        jobs = await Job._fetch_jobs(self, jobid=jobid)
        if len(jobs) == 0:
            raise SfApiError(f"Job not found: ${jobid}")

        return jobs[0]

    async def jobs(
        self,
        user: Optional[str] = None,
        partition: Optional[str] = None,
        command: Optional[JobCommand] = JobCommand.squeue,
    ) -> List["Job"]:
        Job = JobSacct if (command == JobCommand.sacct) else JobSqueue

        return await Job._fetch_jobs(self, user=user, partition=partition)

    async def ls(self, path) -> List[RemotePath]:
        r = await self.client.get(f"utilities/ls/{self.name}/{path}")

        json_response = r.json()
        directory_listing_response = DirectoryListingResponse.parse_obj(json_response)
        if directory_listing_response.status == DirectoryListingResponseStatus.ERROR:
            raise SfApiError(directory_listing_response.error)

        paths = []

        def _to_remote_path(path, entry):
            kwargs = entry.dict()
            kwargs.update(path=path)
            p = RemotePath(**kwargs)
            p.compute = self

            return p

        # Special case for listing file
        if len(directory_listing_response.entries) == 1:
            entry = directory_listing_response.entries[0]
            # The API can add an extra /
            path = entry.name
            if entry.name.startswith("//"):
                path = path[1:]
            filename = PurePosixPath(path).name
            entry.name = filename
            paths.append(_to_remote_path(path, entry))
        else:
            for entry in directory_listing_response.entries:
                paths.append(_to_remote_path(f"{path}/{entry.name}", entry))

        return paths
