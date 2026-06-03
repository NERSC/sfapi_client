import time
from pathlib import Path

from sfapi_client.jobs import JobState
from sfapi_client.compute import CommandTask, TaskStatus


def _periodic_command():
    return "bash -lc 'i=0; while [ $i -lt 30 ]; do echo tick-$i; i=$((i+1)); sleep 1; done'"


def _failing_command():
    return "bash -lc 'echo failing >&2; exit 1'"


def _poll_task(task, predicate, timeout=60, pause=1):
    deadline = time.time() + timeout

    while True:
        task.update()
        if predicate(task):
            return task

        if time.time() >= deadline:
            raise AssertionError(
                f"task did not reach the expected state within {timeout}s"
            )

        time.sleep(pause)


def test_compute(authenticated_client, test_machine):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        assert machine.status in ["active", "unavailable", "degraded", "other"]
        assert machine.name == test_machine.value


def test_job(authenticated_client, test_job_path, test_machine):
    with authenticated_client as client:
        machine = client.compute(test_machine)

        job = machine.submit_job(test_job_path)
        job.complete()
        assert job.state == JobState.COMPLETED

        job_looked_up = machine.job(job.jobid)

        assert job.jobid == job_looked_up.jobid


def test_fetch_jobs(authenticated_client, test_machine, test_username):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        machine.jobs(user=test_username)


def test_list_dir_contents(authenticated_client, test_machine, test_job_path):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        test_job = Path(test_job_path)
        test_path = test_job.parent
        test_name = test_job.name

        paths = machine.ls(test_path)

        found = False
        for p in paths:
            if p.name == test_name:
                found = True
                break

        assert found


def test_list_dir(authenticated_client, test_machine, test_job_path):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        test_job = Path(test_job_path)
        test_path = test_job.parent

        paths = machine.ls(test_path, directory=True)
        assert len(paths) == 1
        assert paths[0].name == test_path.name


def test_list_file(authenticated_client, test_machine, test_job_path):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        test_job_filename = Path(test_job_path).name

        paths = machine.ls(test_job_path)

        found = False
        for p in paths:
            if p.name == test_job_filename:
                found = True
                break

        assert found


def test_run_arg_list(authenticated_client, test_machine, test_job_path):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        output = machine.run(["ls", test_job_path])

        assert test_job_path in output


def test_run_arg_str(authenticated_client, test_machine, test_job_path):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        output = machine.run(f"ls {test_job_path}")

        assert test_job_path in output


def test_run_arg_path(authenticated_client, test_machine):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        [remote_path] = machine.ls("/usr/bin/hostname")
        output = machine.run(remote_path)

        assert output


def test_run_task(authenticated_client, test_machine):
    with authenticated_client as client:
        machine = client.compute(test_machine)

        task = machine.run_task("echo hello")

        assert isinstance(task, CommandTask)
        assert task.id
        assert task.status is None
        assert task.result is None


def test_run_task_wait(authenticated_client, test_machine):
    with authenticated_client as client:
        machine = client.compute(test_machine)

        task = machine.run_task("echo hello")
        _poll_task(task, lambda t: t.status is TaskStatus.COMPLETED)

        assert task.status is TaskStatus.COMPLETED
        assert task.result is not None
        assert task.result.output is not None
        assert "hello" in task.result.output
        assert task.result.error in ("", None)


def test_run_task_update(authenticated_client, test_machine):
    with authenticated_client as client:
        machine = client.compute(test_machine)

        task = machine.run_task(_periodic_command())
        updated = _poll_task(
            task,
            lambda t: t.result is not None and t.status is TaskStatus.COMPLETED,
            timeout=90,
        )

        assert updated is task
        assert task.status is TaskStatus.COMPLETED
        assert task.result is not None
        assert task.result.output is not None
        assert "tick-" in task.result.output


def test_run_task_cancel(authenticated_client, test_machine):
    with authenticated_client as client:
        machine = client.compute(test_machine)

        task = machine.run_task(_periodic_command())
        time.sleep(2)
        task.cancel()

        _poll_task(task, lambda t: t.status is TaskStatus.CANCELLED, timeout=90)
        assert task.status == TaskStatus.CANCELLED


def test_run_task_error(authenticated_client, test_machine):
    with authenticated_client as client:
        machine = client.compute(test_machine)

        task = machine.run_task(_failing_command())
        _poll_task(task, lambda t: t.status is TaskStatus.COMPLETED, timeout=90)

        assert task.status is TaskStatus.COMPLETED
        assert task.result is not None
        assert task.result.error == "failing\n"
        assert task.result.output == ""
        assert task.result.exit_code == 1
        assert task.result.status == "error"
