import asyncio
from typing import List, Optional
import json
from enum import Enum
from pydantic import BaseModel

from .common import SfApiError, _SLEEP
from .job import Job
from ._models import (
    AppRoutersStatusModelsStatus as ComputeBase,
    AppRoutersComputeModelsStatus as JobStatus,
    PublicHost as Machines,
    Task,
    JobStatusResponseSacct,
    JobStatusResponseSqueue,
)


class SubmitJobResponseStatus(Enum):
    OK = "OK"
    ERROR = "ERROR"


class SubmitJobResponse(BaseModel):
    task_id: str
    status: SubmitJobResponseStatus
    error: Optional[str]


class Compute(ComputeBase):
    client: Optional["Client"]

    def submit_job(self, batch_submit_filepath: str) -> "Job":
        data = {"job": batch_submit_filepath, "isPath": True}

        r = self.client.post(f"compute/jobs/{self.name}", data)
        r.raise_for_status()

        json_response = r.json()
        job_response = SubmitJobResponse.parse_obj(json_response)

        if job_response.status == SubmitJobResponseStatus.ERROR:
            raise SfApiError(job_response.error)

        task_id = job_response.task_id

        # We now need to poll waiting for the task to complete!
        while True:
            r = self.client.get(f"tasks/{task_id}")
            r.raise_for_status()

            json_response = r.json()
            task = Task.parse_obj(json_response)

            if task.status.lower() in ["error", "failed"]:
                raise SfApiError(task.result)

            if task.result is None:
                _SLEEP(1)
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

    def _fetch_job_status(self, jobid: int):
        params = {"sacct": True}
        JobStatusResponse = JobStatusResponseSacct
        r = self.client.get(f"compute/jobs/{self.name}/{jobid}", params)

        json_response = r.json()
        job_status = JobStatusResponse.parse_obj(json_response)

        if job_status.status == JobStatus.ERROR:
            error = job_status.error
            raise SfApiError(error)

        output = job_status.output

        return output[0]

    def job(self, jobid: int) -> "Job":
        job_status = self._fetch_job_status(jobid)

        job = Job.parse_obj(job_status)
        job.compute = self

        return job
