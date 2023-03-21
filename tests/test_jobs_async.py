import pytest

from sfapi_client import AsyncClient
from sfapi_client import JobState
from sfapi_client import Machines


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