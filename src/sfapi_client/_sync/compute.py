from typing import Dict, List, Optional, Union
import json
from pydantic import PrivateAttr, ConfigDict, BaseModel
from ..exceptions import SfApiError
from .._utils import _SLEEP
from .jobs import JobSacct, JobSqueue, JobCommand
from .._models import (
    AppRoutersStatusModelsStatus as ComputeBase,
    Task as TaskResponse,
    PublicHost as Machine,
    BodyRunCommandUtilitiesCommandMachinePost as RunCommandBody,
    AppRoutersComputeModelsCommandOutput as RunCommandResponse,
    AppRoutersComputeModelsStatus as RunCommandResponseStatus,
)
from .paths import RemotePath
from .._monitor import SyncJobMonitor
from .._compute import SubmitJobResponse, SubmitJobResponseStatus, TaskStatus
from .._utils import check_auth

# Patch to return str names from Enum of py3.11
Machine.__str__ = lambda self: self.value


class CommandTaskResult(BaseModel):
    """
    Result data returned by a command execution task.
    """

    model_config = ConfigDict(extra="allow")

    status: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None


class CommandTask(BaseModel):
    """
    Models an asynchronous command execution task.
    """

    compute: "Compute"
    id: str
    status: Optional[TaskStatus] = None
    result: Optional[CommandTaskResult] = None

    def _fetch(self) -> TaskResponse:
        """
        Fetch the latest task state from the API.

        :return: The raw task response returned by the API.
        """
        r = self.compute.client.get(f"tasks/{self.id}")
        json_response = r.json()

        return TaskResponse.model_validate(json_response)

    def update(self):
        """
        Refresh the task state.

        :return: The updated task instance.
        """
        task = self._fetch()
        if task.status is not None:
            # Map the status return by the API (lowercase string) to our TaskStatus enum ( uppercase )
            # We do this for consistency as all our enums are uppercase
            self.status = TaskStatus[task.status.upper()]

        if task.result is not None:
            self.result = CommandTaskResult.model_validate_json(task.result)

        return self

    def _wait(self):
        while True:
            self.update()

            if self.status in [
                TaskStatus.COMPLETED,
                TaskStatus.CANCELLED,
                TaskStatus.FAILED,
            ]:
                return self

            _SLEEP(1)

    def __await__(self):
        return self._wait().__await__()

    def cancel(self):
        """
        Cancel the running task.
        """
        self.compute.client.delete(f"tasks/{self.id}")


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

    def _wait_for_task(self, task_id) -> CommandTaskResult:

        task = CommandTask(compute=self, id=task_id)

        while True:
            task.update()

            if task.status is TaskStatus.FAILED:
                raise SfApiError(task.result)

            if task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                _SLEEP(1)
                continue

            return task.result

    @check_auth
    def submit_job(self, script: Union[str, RemotePath], args: Optional[List[str]] = None) -> JobSqueue:
        """Submit a job to the compute resource

        :param script: Path to file on the compute system, or script to run beginning with `#!`.
        :param args: An optional list of command line arguments to pass to the script.
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
        if args is not None:
            if not is_path:
                raise ValueError("Command line arguments cannot be passed when the script is not a file.")
            data["args"] = args

        r = self.client.post(f"compute/jobs/{self.name}", data)
        r.raise_for_status()

        json_response = r.json()
        job_response = SubmitJobResponse.model_validate(json_response)

        if job_response.status == SubmitJobResponseStatus.ERROR:
            raise SfApiError(job_response.error)

        task_id = job_response.task_id

        # We now need waiting for the task to complete!
        task_result = self._wait_for_task(task_id)
        if task_result.status == "error":
            raise SfApiError(task_result.error)

        # Get the jobid from the extra fields of the result
        jobid = task_result.__pydantic_extra__.get("jobid")
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
        task = self._run_task(args)
        task._wait()

        if task.result.error:
            raise SfApiError(task.result.error)

        return task.result.output

    def _run_task(
        self, args: Union[str, RemotePath, List[str]]
    ) -> CommandTask:
        body: RunCommandBody = {
            "executable": args if not isinstance(args, list) else " ".join(args)
        }

        r = self.client.post(f"utilities/command/{self.name}", data=body)
        json_response = r.json()
        run_response = RunCommandResponse.model_validate(json_response)
        if run_response.status == RunCommandResponseStatus.ERROR:
            raise SfApiError(run_response.error)

        return CommandTask(compute=self, id=run_response.task_id)

    @check_auth
    def run_task(
        self, args: Union[str, RemotePath, List[str]]
    ) -> CommandTask:
        """
        Submit a command to the compute resource and return a task.

        :param args: Command to execute.
        :return: Task object that can be awaited ( version ), updated, or cancelled.
        """
        return self._run_task(args)

    def outages(self):
        return self.client.resources.outages(self.name)

    def planned_outages(self):
        return self.client.resources.planned_outages(self.name)
