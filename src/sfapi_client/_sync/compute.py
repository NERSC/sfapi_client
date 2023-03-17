import asyncio
from typing import Dict, List, Optional, Union
import json
from enum import Enum
from pydantic import BaseModel


from ..common import SfApiError, _SLEEP
from .job import JobSacct, JobSqueue, JobSqueue, JobCommand
from .._models import (
    AppRoutersStatusModelsStatus as ComputeBase,
    Task,
    PublicHost as Machines,
    BodyRunCommandUtilitiesCommandMachinePost as RunCommandBody,
    AppRoutersComputeModelsCommandOutput as RunCommandResponse,
    AppRoutersComputeModelsStatus as RunCommandResponseStatus,
)
from .path import RemotePath


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


class Compute(ComputeBase):
    client: Optional["Client"]

    def dict(self, *args, **kwargs) -> Dict:
        if "exclude" not in kwargs:
            kwargs["exclude"] = {"client"}
        return super().dict(*args, **kwargs)

    def _wait_for_task(self, task_id) -> str:
        while True:
            r = self.client.get(f"tasks/{task_id}")

            json_response = r.json()
            task = Task.parse_obj(json_response)

            if task.status.lower() in ["error", "failed"]:
                raise SfApiError(task.result)

            if task.result is None:
                _SLEEP(1)
                continue

            return task.result

    def submit_job(self, batch_submit_filepath: str) -> "Job":
        data = {"job": batch_submit_filepath, "isPath": True}

        r = self.client.post(f"compute/jobs/{self.name}", data)
        r.raise_for_status()

        json_response = r.json()
        job_response = SubmitJobResponse.parse_obj(json_response)

        if job_response.status == SubmitJobResponseStatus.ERROR:
            raise SfApiError(job_response.error)

        task_id = job_response.task_id

        # We now need waiting for the task to complete!
        task_result = self._wait_for_task(task_id)
        result = json.loads(task_result)
        if result.get("status") == "error":
            raise SfApiError(result["error"])

        jobid = result.get("jobid")
        if jobid is None:
            raise SfApiError(f"Unable to extract jobid if for task: {task_id}")

        job = JobSqueue(jobid=jobid)
        job.compute = self

        return job

    def job(
        self, jobid: int, command: Optional[JobCommand] = JobCommand.sacct
    ) -> "Union[JobSacct, JobSqueue]":
        # Get different job depending on query
        Job = JobSacct if (command == JobCommand.sacct) else JobSqueue
        jobs = Job._fetch_jobs(self, jobid=jobid)
        if len(jobs) == 0:
            raise SfApiError(f"Job not found: ${jobid}")

        return jobs[0]

    def jobs(
        self,
        user: Optional[str] = None,
        partition: Optional[str] = None,
        command: Optional[JobCommand] = JobCommand.squeue,
    ) -> List["Job"]:
        Job = JobSacct if (command == JobCommand.sacct) else JobSqueue

        return Job._fetch_jobs(self, user=user, partition=partition)

    def ls(self, path, directory=False) -> List[RemotePath]:
        return RemotePath._ls(self, path, directory)

    def run(self, args: Union[str, RemotePath, List[str]]):
        body: RunCommandBody = {
            "executable": args if not isinstance(args, list) else " ".join(args)
        }

        r = self.client.post(f"utilities/command/{self.name}", data=body)
        json_response = r.json()
        run_response = RunCommandResponse.parse_obj(json_response)
        if run_response.status == RunCommandResponseStatus.ERROR:
            raise SfApiError(run_response.error)

        task_id = run_response.task_id
        task_result = self._wait_for_task(task_id)
        command_result = CommandResult.parse_raw(task_result)
        if command_result.status == "error":
            raise SfApiError(command_result.error)

        return command_result.output
