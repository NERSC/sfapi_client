import pytest

from sfapi_client import AsyncClient
from sfapi_client import JobState
from sfapi_client import Machines


@pytest.mark.asyncio
async def test_compute(client_id, client_secret, test_machine):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)

        assert machine.name == test_machine.value


@pytest.mark.asyncio
async def test_job(client_id, client_secret, test_job_path, test_machine):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)

        job = await machine.submit_job(test_job_path)
        await job.complete()
        assert job.state == JobState.COMPLETED

        job_looked_up = await machine.job(job.jobid)

        assert job.jobid == job_looked_up.jobid


@pytest.mark.asyncio
async def test_fetch_jobs(client_id, client_secret, test_machine, test_username):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        await machine.jobs(user=test_username)
