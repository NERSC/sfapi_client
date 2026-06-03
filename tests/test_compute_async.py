import asyncio

import pytest
from pathlib import Path

from sfapi_client.compute import AsyncCommandTask, TaskStatus
from sfapi_client.jobs import JobState


def _periodic_command():
    return "bash -lc 'i=0; while [ $i -lt 30 ]; do echo tick-$i; i=$((i+1)); sleep 1; done'"


def _failing_command():
    return "bash -lc 'echo failing >&2; exit 1'"


async def _poll_task(task, predicate, timeout=60, pause=1):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout

    while True:
        await task.update()
        if predicate(task):
            return task

        if loop.time() >= deadline:
            raise AssertionError(
                f"task did not reach the expected state within {timeout}s"
            )

        await asyncio.sleep(pause)


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
async def test_run_task(async_authenticated_client, test_machine):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)

        task = await machine.run_task("echo hello")

        assert isinstance(task, AsyncCommandTask)
        assert task.id
        assert task.status is None
        assert task.result is None


@pytest.mark.asyncio
async def test_run_task_await(async_authenticated_client, test_machine):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)

        task = await machine.run_task("echo hello")
        awaited = await task

        assert awaited is task
        assert task.status is TaskStatus.COMPLETED
        assert task.result is not None
        assert task.result.output == "hello\n"
        assert task.result.error == ""


@pytest.mark.asyncio
async def test_run_task_update(async_authenticated_client, test_machine):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)
        task = await machine.run_task(_periodic_command())

        updated = await _poll_task(
            task,
            lambda t: (
                t.result is not None
                and t.result.output is not None
                and t.status is TaskStatus.COMPLETED
            ),
        )

        assert updated is task


@pytest.mark.asyncio
async def test_run_task_cancel(async_authenticated_client, test_machine):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)

        task = await machine.run_task(_periodic_command())
        await asyncio.sleep(2)
        await task.cancel()

        await _poll_task(task, lambda t: t.status == TaskStatus.CANCELLED, timeout=90)

        assert task.status == TaskStatus.CANCELLED


@pytest.mark.asyncio
async def test_run_task_error(async_authenticated_client, test_machine):
    async with async_authenticated_client as client:
        machine = await client.compute(test_machine)

        task = await machine.run_task(_failing_command())
        await task

        assert task.status is TaskStatus.COMPLETED
        assert task.result is not None
        assert task.result.error == "failing\n"
        assert task.result.output == ""
        assert task.result.exit_code == 1
        assert task.result.status == "error"


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
