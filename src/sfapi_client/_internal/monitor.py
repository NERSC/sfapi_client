import asyncio
from asyncio import Future
from typing import Union, Optional, List, Set, Dict, Type
from abc import ABC, abstractmethod

from .._async.job import JobCommand
from .._async.job import (
    _fetch_jobs as _fetch_jobs_async,
    JobSacct as AsyncJobSacct,
    JobSqueue as AsyncJobSqueue,
)
from .._sync.job import _fetch_jobs, JobSacct, JobSqueue


# Async monitor that batches request for job state into fewer request by
# requesting that state of multiple jobs in a single request to the server.
class AsyncJobMonitor:
    def __init__(self, compute: "Compute"):
        self._jobids: Dict[Type, Set[int]] = {}
        self._compute: "Compute" = compute
        self._monitor_task: asyncio.Task = None
        self._futures: Dict[Type, Future] = {}
        self._last_job_type_fetched: Type = None

    async def _create_task(self):
        job_type = self._job_type_to_fetch()
        jobids = self._jobids[job_type]
        del self._jobids[job_type]
        self._monitor_task = asyncio.create_task(self._monitor(job_type, jobids))

        # If we have a future waiting then we need to hook it up
        future = self._futures.get(job_type)
        if future is not None:
            del self._futures[job_type]
            jobs = await self._monitor_task
            future.set_result(jobs)

    # Round robin job types if we have both
    def _job_type_to_fetch(self):
        current_job_types = list(self._jobids.keys())

        if len(current_job_types) == 1:
            return current_job_types[0]

        possible_job_types = [AsyncJobSqueue, AsyncJobSacct]

        index_of_next_type = 0

        if self._last_job_type_fetched is not None:
            index_of_next_type = (
                possible_job_types.index(self._last_job_type_fetched) + 1
            ) % len(possible_job_types)

        while True:
            job_type = possible_job_types[index_of_next_type]
            if job_type in current_job_types:
                break
            index_of_next_type = (index_of_next_type + 1) % len(possible_job_types)

        self._last_job_type_fetched = job_type

        return job_type

    async def fetch_jobs(
        self, job_type: Union["JobSacct", "JobSqueue"], jobids: List[int]
    ) -> List[Union["AsyncJobSacct", "AsyncJobSqueue"]]:
        jobids_for_type = self._jobids.setdefault(job_type, set())
        jobids_for_type.update(jobids)

        if self._monitor_task is None:
            await self._create_task()
            jobs = await self._monitor_task
            # process jobs and return
        # Monitoring task is already running, so we have to wait for the next one
        else:
            future = self._futures.setdefault(
                job_type, asyncio.get_event_loop().create_future()
            )
            jobs = await future

        # Now filter the jobs we where looking for
        fetched_jobids = list(jobs.keys())
        return [jobs[i] for i in jobids if i in fetched_jobids]

    async def _monitor(
        self, job_type: Union[AsyncJobSqueue, AsyncJobSacct], jobids: Set[int]
    ):
        jobs = await _fetch_jobs_async(
            job_type=job_type, compute=self._compute, jobids=jobids
        )

        jobs_by_id = {j.jobid: j for j in jobs}

        # If we have more jobs schedule the monitor task again
        if self._jobids:
            await self._create_task()
        else:
            self._monitor_task = None

        return jobs_by_id


# Pass through implementation for sync client. In the future a threaded monitor could probably be
# implemented, it would probably require the sync interfaces to return Futures, so would require
# breaking changes.
class SyncJobMonitor:
    def __init__(self, compute: "Compute"):
        self._compute = compute

    def fetch_jobs(
        self, job_type: Union["JobSacct", "JobSqueue"], jobids: List[int]
    ) -> List[Union[JobSqueue, JobSacct]]:
        return _fetch_jobs(job_type=job_type, compute=self._compute, jobids=jobids)
