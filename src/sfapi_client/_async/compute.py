import asyncio
from typing import Dict, List, Optional, Union
import json
from enum import Enum
from pydantic import BaseModel, PrivateAttr


from ..exceptions import SfApiError
from .._utils import _ASYNC_SLEEP
from .jobs import AsyncJobSacct, AsyncJobSqueue, AsyncJobSqueue, JobCommand
from .._models import (
    AppRoutersStatusModelsStatus as ComputeBase,
    Task,
    PublicHost as Machines,
    BodyRunCommandUtilitiesCommandMachinePost as RunCommandBody,
    AppRoutersComputeModelsCommandOutput as RunCommandResponse,
    AppRoutersComputeModelsStatus as RunCommandResponseStatus,
)
from .paths import AsyncRemotePath
from .._internal.monitor import AsyncJobMonitor
from .._compute import CommandResult, SubmitJobResponse, SubmitJobResponseStatus


class AsyncCompute(ComputeBase):
    client: Optional["AsyncClient"]
    _monitor: AsyncJobMonitor = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._monitor = AsyncJobMonitor(self)

    def dict(self, *args, **kwargs) -> Dict:
        if "exclude" not in kwargs:
            kwargs["exclude"] = {"client"}
        return super().dict(*args, **kwargs)

    async def _wait_for_task(self, task_id) -> str:
        while True:
            r = await self.client.get(f"tasks/{task_id}")

            json_response = r.json()
            task = Task.parse_obj(json_response)

            if task.status.lower() in ["error", "failed"]:
                raise SfApiError(task.result)

            if task.result is None:
                await _ASYNC_SLEEP(1)
                continue

            return task.result

    async def submit_job(self, batch_submit_filepath: str) -> "Job":
        data = {"job": batch_submit_filepath, "isPath": True}

        r = await self.client.post(f"compute/jobs/{self.name}", data)
        r.raise_for_status()

        json_response = r.json()
        job_response = SubmitJobResponse.parse_obj(json_response)

        if job_response.status == SubmitJobResponseStatus.ERROR:
            raise SfApiError(job_response.error)

        task_id = job_response.task_id

        # We now need waiting for the task to complete!
        task_result = await self._wait_for_task(task_id)
        result = json.loads(task_result)
        if result.get("status") == "error":
            raise SfApiError(result["error"])

        jobid = result.get("jobid")
        if jobid is None:
            raise SfApiError(f"Unable to extract jobid if for task: {task_id}")

        job = AsyncJobSqueue(jobid=jobid)
        job.compute = self

        return job

    async def job(
        self, jobid: int, command: Optional[JobCommand] = JobCommand.sacct
    ) -> Union["AsyncJobSacct", "AsyncJobSqueue"]:
        # Get different job depending on query
        Job = AsyncJobSacct if (command == JobCommand.sacct) else AsyncJobSqueue
        jobs = await self._monitor.fetch_jobs(job_type=Job, jobids=[jobid])
        if len(jobs) == 0:
            raise SfApiError(f"Job not found: ${jobid}")

        return jobs[0]

    async def jobs(
        self,
        jobids: Optional[int] = None,
        user: Optional[str] = None,
        partition: Optional[str] = None,
        command: Optional[JobCommand] = JobCommand.squeue,
    ) -> List[Union[AsyncJobSacct, AsyncJobSqueue]]:
        Job = AsyncJobSacct if (command == JobCommand.sacct) else AsyncJobSqueue

        # If we have been given just jobids, use the monitor
        if jobids is not None and user is None and partition is None:
            return await self._monitor.fetch_jobs(job_type=Job, jobids=jobids)
        else:
            return await Job._fetch_jobs(
                self, jobids=jobids, user=user, partition=partition
            )

    async def ls(self, path, directory=False) -> List[AsyncRemotePath]:
        return await AsyncRemotePath._ls(self, path, directory)

    async def run(self, args: Union[str, AsyncRemotePath, List[str]]):
        body: RunCommandBody = {
            "executable": args if not isinstance(args, list) else " ".join(args)
        }

        r = await self.client.post(f"utilities/command/{self.name}", data=body)
        json_response = r.json()
        run_response = RunCommandResponse.parse_obj(json_response)
        if run_response.status == RunCommandResponseStatus.ERROR:
            raise SfApiError(run_response.error)

        task_id = run_response.task_id
        task_result = await self._wait_for_task(task_id)
        command_result = CommandResult.parse_raw(task_result)
        if command_result.status == "error":
            raise SfApiError(command_result.error)

        return command_result.output

    async def outages(self):
        return await self.client.resources.outages(self.name)

    async def planned_outages(self):
        return await self.client.resources.planned_outages(self.name)
