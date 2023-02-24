import pytest

from sfapi_client import AsyncClient
from sfapi_client import JobState
from sfapi_client import Machines


@pytest.mark.asyncio
async def test_submit(client_id, client_secret, test_job_path):
    async with AsyncClient(client_id, client_secret) as client:
        perl = await client.compute(Machines.perlmutter)
        job = await perl.submit_job(test_job_path)

        await job.complete()

        assert job.state == JobState.COMPLETED


@pytest.mark.asyncio
async def test_cancel(client_id, client_secret, test_job_path):
    async with AsyncClient(client_id, client_secret) as client:
        perl = await client.compute(Machines.perlmutter)
        job = await perl.submit_job(test_job_path)

        await job.cancel()


@pytest.mark.asyncio
async def test_cancel_wait_for_it(client_id, client_secret, test_job_path):
    async with AsyncClient(client_id, client_secret) as client:
        perl = await client.compute(Machines.perlmutter)
        job = await perl.submit_job(test_job_path)

        await job.cancel(wait=True)

        assert job.state == JobState.CANCELLED
