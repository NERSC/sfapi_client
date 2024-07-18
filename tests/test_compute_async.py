import pytest
from pathlib import Path

from sfapi_client.jobs import JobState


@pytest.mark.asyncio
async def test_compute(async_authenticated_client, test_machine):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        assert machine.status in ["active", "unavailable", "degraded", "other"]
        assert machine.name == test_machine.value


@pytest.mark.asyncio
async def test_job(async_authenticated_client, test_job_path, test_machine):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)

        job = await machine.submit_job(test_job_path)
        await job.complete()
        assert job.state == JobState.COMPLETED

        job_looked_up = await machine.job(job.jobid)

        assert job.jobid == job_looked_up.jobid


@pytest.mark.asyncio
async def test_fetch_jobs(async_authenticated_client, test_machine, test_username):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        await machine.jobs(user=test_username)


@pytest.mark.asyncio
async def test_list_dir_contents(
    async_authenticated_client, test_machine, test_job_path
):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        test_job = Path(test_job_path)
        test_path = test_job.parent
        test_name = test_job.name

        paths = await machine.ls(test_path)

        found = False
        for p in paths:
            if p.name == test_name:
                found = True
                break

        assert found


@pytest.mark.asyncio
async def test_list_dir(async_authenticated_client, test_machine, test_job_path):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        test_job = Path(test_job_path)
        test_path = test_job.parent

        paths = await machine.ls(test_path, directory=True)
        assert len(paths) == 1
        assert paths[0].name == test_path.name


@pytest.mark.asyncio
async def test_list_file(async_authenticated_client, test_machine, test_job_path):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        test_job_filename = Path(test_job_path).name
        test_job_dir = Path(test_job_path).parent

        paths = await machine.ls(test_job_path)

        found = False
        for p in paths:
            if p.name == test_job_filename and str(p.parent) == str(test_job_dir):
                found = True
                break

        assert found


@pytest.mark.asyncio
async def test_run_arg_list(async_authenticated_client, test_machine, test_job_path):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        output = await machine.run(["ls", test_job_path])

        assert test_job_path in output


@pytest.mark.asyncio
async def test_run_arg_str(async_authenticated_client, test_machine, test_job_path):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        output = await machine.run(f"ls {test_job_path}")

        assert test_job_path in output


@pytest.mark.asyncio
async def test_run_arg_path(async_authenticated_client, test_machine):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        [remote_path] = await machine.ls("/usr/bin/hostname")
        output = await machine.run(remote_path)

        assert output


@pytest.mark.asyncio
async def test_outages(async_authenticated_client, test_machine):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        outages = await machine.outages()

        assert len(outages) > 0


@pytest.mark.asyncio
async def test_planned_outages(async_authenticated_client, test_machine):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        outages = await machine.planned_outages()

        assert len(outages) >= 0
