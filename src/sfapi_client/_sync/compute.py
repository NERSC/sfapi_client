from typing import Dict, List, Optional, Union, Callable
import json
from pydantic import PrivateAttr, ConfigDict
from ..exceptions import SfApiError
from .._utils import _SLEEP
from .jobs import JobSacct, JobSqueue, JobCommand
from .._models import (
    AppRoutersStatusModelsStatus as ComputeBase,
    Task,
    StatusValue,
    PublicHost as Machine,
    BodyRunCommandUtilitiesCommandMachinePost as RunCommandBody,
    AppRoutersComputeModelsCommandOutput as RunCommandResponse,
    AppRoutersComputeModelsStatus as RunCommandResponseStatus,
)
from .paths import RemotePath
from .._monitor import SyncJobMonitor
from .._compute import CommandResult, SubmitJobResponse, SubmitJobResponseStatus

# Patch to return str names from Enum of py3.11
Machine.__str__ = lambda self: self.value


def check_auth(method: Callable):
    def wrapper(self, *args, **kwargs):
        if self.client._client_id is None and self.client._access_token is None:
            raise SfApiError(
                f"Cannot call {self.__class__.__name__}.{method.__name__}() with an unauthenticated client."  # noqa: E501
            )
        elif self.status in [StatusValue.unavailable]:
            raise SfApiError(
                f"Compute resource {self.name} is {self.status.name}, {self.notes}"
            )
        return method(self, *args, **kwargs)

    return wrapper


class Compute(ComputeBase):
    client: Optional["Client"]  # noqa: F821
    _monitor: SyncJobMonitor = PrivateAttr()

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._monitor = SyncJobMonitor(self)

    def dict(self, *args, **kwargs) -> Dict:
        if "exclude" not in kwargs:
            kwargs["exclude"] = {"client"}
        return super().dict(*args, **kwargs)

    def _wait_for_task(self, task_id) -> str:
        while True:
            r = self.client.get(f"tasks/{task_id}")

            json_response = r.json()
            task = Task.model_validate(json_response)

            if task.status.lower() in ["error", "failed"]:
                raise SfApiError(task.result)

            if task.result is None:
                _SLEEP(1)
                continue

            return task.result

    @check_auth
    def submit_job(self, script: Union[str, RemotePath]) -> JobSqueue:
        """Submit a job to the compute resource

        :param script: Path to file on the compute system, or script to run beginning with `#!`.
        :return: Object containing information about the job, its job id, and status on the system.
        """

        is_path: bool = True

        # If it's a remote path we've already checked so just continue
        if isinstance(script, RemotePath):
            pass
        # If the string input looks like a script we'll set is_path to false
        elif script.startswith("#!") and "\n" in script:
            # If it starts with shebang and has multiple lines
            is_path = False
        else:
            # If we're given a path make sure it exists
            script_path = self.ls(script)
            is_file = script_path[0].is_file()
            if len(script_path) != 1 or not is_file:
                raise SfApiError(f"Script path not present or is not a file, {script}")

        data = {"job": script, "isPath": is_path}

        r = self.client.post(f"compute/jobs/{self.name}", data)
        r.raise_for_status()

        json_response = r.json()
        job_response = SubmitJobResponse.model_validate(json_response)

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

        job = JobSqueue(jobid=jobid, compute=self)

        return job

    @check_auth
    def job(
        self, jobid: Union[int, str], command: Optional[JobCommand] = JobCommand.sacct
    ) -> Union["JobSacct", "JobSqueue"]:
        # Get different job depending on query
        Job = JobSacct if (command == JobCommand.sacct) else JobSqueue
        jobs = self._monitor.fetch_jobs(job_type=Job, jobids=[jobid])
        if len(jobs) == 0:
            raise SfApiError(f"Job not found: {jobid}")

        return jobs[0]

    @check_auth
    def jobs(
        self,
        jobids: Optional[List[Union[int, str]]] = None,
        user: Optional[str] = None,
        partition: Optional[str] = None,
        command: Optional[JobCommand] = JobCommand.squeue,
    ) -> List[Union[JobSacct, JobSqueue]]:
        Job = JobSacct if (command == JobCommand.sacct) else JobSqueue

        # If we have been given just jobids, use the monitor
        if jobids is not None and user is None and partition is None:
            return self._monitor.fetch_jobs(job_type=Job, jobids=jobids)
        else:
            return Job._fetch_jobs(
                self, jobids=jobids, user=user, partition=partition
            )

    @check_auth
    def ls(self, path, directory=False) -> List[RemotePath]:
        return RemotePath._ls(self, path, directory)

    @check_auth
    def run(self, args: Union[str, RemotePath, List[str]]):
        body: RunCommandBody = {
            "executable": args if not isinstance(args, list) else " ".join(args)
        }

        r = self.client.post(f"utilities/command/{self.name}", data=body)
        json_response = r.json()
        run_response = RunCommandResponse.model_validate(json_response)
        if run_response.status == RunCommandResponseStatus.ERROR:
            raise SfApiError(run_response.error)

        task_id = run_response.task_id
        task_result = self._wait_for_task(task_id)
        command_result = CommandResult.model_validate_json(task_result)
        if command_result.status == "error":
            raise SfApiError(command_result.error)

        return command_result.output

    def outages(self):
        return self.client.resources.outages(self.name)

    def planned_outages(self):
        return self.client.resources.planned_outages(self.name)
