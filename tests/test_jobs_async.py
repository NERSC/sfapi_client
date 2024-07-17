import pytest
import asyncio

from sfapi_client import AsyncClient
from sfapi_client.compute import AsyncCompute
from sfapi_client.jobs import AsyncJobSqueue, AsyncJobSacct, JobState


@pytest.mark.asyncio
async def test_submit(async_authenticated_client, test_job_path, test_machine):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        job = await machine.submit_job(test_job_path)

        state = await job.complete()

        assert state == JobState.COMPLETED


@pytest.mark.asyncio
async def test_cancel(async_authenticated_client, test_job_path, test_machine):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        job = await machine.submit_job(test_job_path)

        await job.cancel()


@pytest.mark.asyncio
async def test_cancel_wait_for_it(
    async_authenticated_client, test_job_path, test_machine
):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        job = await machine.submit_job(test_job_path)

        await job.cancel(wait=True)

        assert job.state == JobState.CANCELLED


@pytest.mark.asyncio
async def test_running(async_authenticated_client, test_job_path, test_machine):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        job = await machine.submit_job(test_job_path)

        state = await job.running()

        assert state == JobState.RUNNING


@pytest.mark.asyncio
async def test_complete_timeout(
    async_authenticated_client, test_job_path, test_machine
):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        job = await machine.submit_job(test_job_path)

        with pytest.raises(TimeoutError):
            await job.complete(timeout=1)


@pytest.mark.asyncio
async def test_job_monitor_check_request(
    async_authenticated_client, mocker, test_job_path, test_machine
):
    async with async_authenticated_client as client:
        _fetch_jobs_async = mocker.patch("sfapi_client._monitor._fetch_jobs_async")
        machine = await client.compute(test_machine)

        # Create some test jobs for mocking
        test_jobs = [
            AsyncJobSqueue(jobid=str(i), compute=machine) for i in range(0, 10)
        ]
        test_jobs_futures = [asyncio.Future() for _ in range(0, 10)]
        for i in range(0, 10):
            test_jobs_futures[i].set_result(test_jobs[i])

        # Patch the submit_job to return the test jobs
        submit_job = mocker.patch.object(AsyncCompute, "submit_job")
        submit_job.side_effect = test_jobs_futures

        # Patch the return value of _fetch_jobs_async to return
        # the test jobs
        _fetch_jobs_async.return_value = test_jobs

        # Submit a bunch on jobs
        jobs = []
        for _ in range(0, 10):
            jobs.append(await machine.submit_job(test_job_path))
        jobs = test_jobs

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
async def test_job_monitor_job_types(async_authenticated_client, mocker, test_machine):
    async with async_authenticated_client as client:
        _fetch_jobs_async = mocker.patch("sfapi_client._monitor._fetch_jobs_async")
        machine = await client.compute(test_machine)

        test_job_specs = [
            (AsyncJobSqueue, 0),
            (AsyncJobSqueue, 1),
            (AsyncJobSacct, 2),
            (AsyncJobSqueue, 3),
        ]

        # Create some test jobs for mocking
        test_jobs = [
            job_class(jobid=str(i), compute=machine)
            for (job_class, i) in test_job_specs
        ]
        test_jobs_futures = [asyncio.Future() for _ in range(len(test_job_specs))]
        for i, f in enumerate(test_jobs_futures):
            f.set_result(test_jobs[i])

        # Patch the job method to return the test jobs
        job = mocker.patch.object(AsyncCompute, "job")
        job.side_effect = test_jobs_futures

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
        assert kwargs["job_type"] == AsyncJobSqueue

        _, kwargs = second_call
        assert kwargs["job_type"] == AsyncJobSqueue

        _, kwargs = third_call
        assert kwargs["job_type"] == AsyncJobSacct


# We currently run this in api-dev as its a new feature deployed there
@pytest.mark.api_dev
@pytest.mark.asyncio
async def test_job_monitor_gather(
    dev_client_id,
    dev_client_secret,
    test_job_path,
    test_machine,
    dev_api_url,
    dev_token_url,
):
    async with AsyncClient(
        client_id=dev_client_id,
        secret=dev_client_secret,
        api_base_url=dev_api_url,
        token_url=dev_token_url,
    ) as client:
        machine = await client.compute(test_machine)

        submit_tasks = []
        for _ in range(0, 5):
            submit_tasks.append(asyncio.create_task(machine.submit_job(test_job_path)))

        jobs = await asyncio.gather(*submit_tasks)

        # Wait for all the jobs to be complete
        await asyncio.gather(*[asyncio.create_task(j.complete()) for j in jobs])

        for j in jobs:
            assert j.state == JobState.COMPLETED
