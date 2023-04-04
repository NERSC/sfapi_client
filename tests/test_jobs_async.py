import pytest
import asyncio

from sfapi_client import AsyncClient
from sfapi_client import JobState
from sfapi_client import Machines
from sfapi_client._async import job
from sfapi_client._async.compute import Compute
from sfapi_client._async.job import JobSqueue, JobSacct, JobCommand


@pytest.mark.asyncio
async def test_submit(client_id, client_secret, test_job_path, test_machine):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        job = await machine.submit_job(test_job_path)

        state = await job.complete()

        assert state == JobState.COMPLETED


@pytest.mark.asyncio
async def test_cancel(client_id, client_secret, test_job_path, test_machine):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        job = await machine.submit_job(test_job_path)

        await job.cancel()


@pytest.mark.asyncio
async def test_cancel_wait_for_it(
    client_id, client_secret, test_job_path, test_machine
):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        job = await machine.submit_job(test_job_path)

        await job.cancel(wait=True)

        assert job.state == JobState.CANCELLED


@pytest.mark.asyncio
async def test_running(client_id, client_secret, test_job_path, test_machine):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        job = await machine.submit_job(test_job_path)

        state = await job.running()

        assert state == JobState.RUNNING


@pytest.mark.asyncio
async def test_running_timeout(client_id, client_secret, test_job_path, test_machine):
    async with AsyncClient(client_id, client_secret, wait_interval=1) as client:
        machine = await client.compute(test_machine)
        job = await machine.submit_job(test_job_path)

        with pytest.raises(TimeoutError):
            await job.running(timeout=1)


@pytest.mark.asyncio
async def test_complete_timeout(client_id, client_secret, test_job_path, test_machine):
    async with AsyncClient(client_id, client_secret, wait_interval=1) as client:
        machine = await client.compute(test_machine)
        job = await machine.submit_job(test_job_path)

        with pytest.raises(TimeoutError):
            await job.complete(timeout=1)


@pytest.mark.asyncio
async def test_job_monitor_check_request(
    mocker, client_id, client_secret, test_job_path, test_machine
):
    async with AsyncClient(client_id, client_secret) as client:
        _fetch_jobs_async = mocker.patch(
            "sfapi_client._internal.monitor._fetch_jobs_async"
        )
        machine = await client.compute(test_machine)

        # Create some test jobs for mocking
        test_jobs = [JobSqueue(jobid=i) for i in range(0, 10)]
        for j in test_jobs:
            j.compute = machine

        # Patch the submit_job to return the test jobs
        submit_job = mocker.patch.object(Compute, "submit_job")
        submit_job.side_effect = test_jobs

        # Patch the return value of _fetch_jobs_async to return
        # the test jobs
        _fetch_jobs_async.return_value = test_jobs

        # Submit a bunch on jobs
        jobs = []
        for _ in range(0, 10):
            jobs.append(await machine.submit_job(test_job_path))

        # Call update on all jobs
        await asyncio.gather(*[asyncio.create_task(j.update()) for j in jobs])

        # We should only hit the server twice
        assert _fetch_jobs_async.await_count == 2

        # We should get two batches of job ids, first one and then
        # the other nine.
        [first_call, second_call] = _fetch_jobs_async.await_args_list
        _, kwargs = first_call
        assert len(kwargs["jobids"]) == 1

        _, kwargs = second_call
        assert len(kwargs["jobids"]) == 9


@pytest.mark.asyncio
async def test_job_monitor_job_types(
    mocker, client_id, client_secret, test_job_path, test_machine
):
    async with AsyncClient(client_id, client_secret) as client:
        _fetch_jobs_async = mocker.patch(
            "sfapi_client._internal.monitor._fetch_jobs_async"
        )
        machine = await client.compute(test_machine)

        test_job_specs = [
            (JobSqueue, 0),
            (JobSqueue, 1),
            (JobSacct, 2),
            (JobSqueue, 3),
        ]

        # Create some test jobs for mocking
        test_jobs = [job_class(jobid=i) for (job_class, i) in test_job_specs]
        for j in test_jobs:
            j.compute = machine

        # Patch the submit_job to return the test jobs
        job = mocker.patch.object(Compute, "job")
        job.side_effect = test_jobs

        # Patch the return value of _fetch_jobs_async to return
        # the test jobs
        _fetch_jobs_async.return_value = test_jobs

        jobs = [
            await machine.job(i, job_class._command)
            for (job_class, i) in test_job_specs
        ]

        # Call update on all jobs
        await asyncio.gather(*[asyncio.create_task(j.update()) for j in jobs])

        # We should only hit the server twice
        assert _fetch_jobs_async.await_count == 3

        # We should get three invocations
        [first_call, second_call, third_call] = _fetch_jobs_async.await_args_list

        _, kwargs = first_call
        assert kwargs["job_type"] == JobSqueue

        _, kwargs = second_call
        assert kwargs["job_type"] == JobSqueue

        _, kwargs = third_call
        assert kwargs["job_type"] == JobSacct


