import asyncio
from typing import List, Optional
import json
from enum import Enum
from pydantic import BaseModel

from .common import SfApiError
from .job import Job


class Machines(str, Enum):
    CORI = "cori"
    PERLMUTTER = "perlmutter"


class Compute(BaseModel):
    client: Optional["Client"]
    name: str
    full_name: str
    description: str
    system_type: str
    notes: List
    status: str

    async def submit_job(self, batch_submit_filepath: str) -> "Job":
        data = {"job": batch_submit_filepath, "isPath": True}

        r = await self.client.post(f"compute/jobs/{self.name}", data)
        r.raise_for_status()

        sfapi_response = r.json()
        if sfapi_response["status"].lower() != "ok":
            raise SfApiError(sfapi_response["error"])

        task_id = sfapi_response["task_id"]

        # We now need to poll waiting for the task to complete!
        while True:
            r = await self.client.get(f"tasks/{task_id}")
            r.raise_for_status()

            sfapi_response = r.json()

            if sfapi_response["status"].lower() == "error":
                raise SfApiError(sfapi_response["error"])

            print(sfapi_response)

            if sfapi_response.get("result") is None:
                await asyncio.sleep(1)
                continue

            results = json.loads(sfapi_response["result"])

            if results["status"].lower() == "error":
                raise SfApiError(results["error"])

            jobid = results.get("jobid")
            if jobid is None:
                raise SfApiError(f"Unable to extract jobid if for task: {task_id}")

            job = Job(jobid=jobid)
            job.compute = self

            return job

    async def job(self, jobid: int) -> "Job":
        job_status = await self.client._fetch_job_status(jobid)

        job = Job.parse_obj(job_status)
        job.compute = self

        return job
