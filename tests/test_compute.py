import pytest

from sfapi_client import Client
from sfapi_client import JobState
from sfapi_client import Machines


@pytest.mark.asyncio
async def test_compute(client_id, client_secret):
    async with Client(client_id, client_secret) as client:
        cori = await client.compute(Machines.CORI)

        assert cori.name == Machines.CORI.value


@pytest.mark.asyncio
async def test_job(client_id, client_secret, test_job_path):
    async with Client(client_id, client_secret) as client:
        cori = await client.compute(Machines.CORI)

        job = await cori.submit_job(test_job_path)
        await job.complete()
        assert job.state == JobState.COMPLETED

        cori_job = await cori.job(job.jobid)

        assert cori_job.jobid == job.jobid
