import pytest

from sfapi_client import Client
from sfapi_client import JobState
from sfapi_client import Machines


@pytest.mark.asyncio
async def test_submit(client_id, client_secret, test_job_path):
    async with Client(client_id, client_secret) as client:
        cori = await client.compute(Machines.CORI)
        job = await cori.submit_job(test_job_path)

        await job.complete()

        assert job.state == JobState.COMPLETED


@pytest.mark.asyncio
async def test_cancel(client_id, client_secret, test_job_path):
    async with Client(client_id, client_secret) as client:
        cori = await client.compute(Machines.CORI)
        job = await cori.submit_job(test_job_path)

        await job.cancel()


@pytest.mark.asyncio
async def test_cancel_wait_for_it(client_id, client_secret, test_job_path):
    async with Client(client_id, client_secret) as client:
        cori = await client.compute(Machines.CORI)
        job = await cori.submit_job(test_job_path)

        await job.cancel(wait=True)

        assert job.state == JobState.CANCELLED
