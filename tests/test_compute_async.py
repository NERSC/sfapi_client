import pytest

from sfapi_client import AsyncClient
from sfapi_client import JobState
from sfapi_client import Machines


@pytest.mark.asyncio
async def test_compute(client_id, client_secret):
    async with AsyncClient(client_id, client_secret) as client:
        perl = await client.compute(Machines.perlmutter)

        assert perl.name == Machines.perlmutter.value


@pytest.mark.asyncio
async def test_job(client_id, client_secret, test_job_path):
    async with AsyncClient(client_id, client_secret) as client:
        perl = await client.compute(Machines.perlmutter)

        job = await perl.submit_job(test_job_path)
        await job.complete()
        assert job.state == JobState.COMPLETED

        perl_job = await perl.job(job.jobid)

        assert perl_job.jobid == job.jobid
