import pytest
from pathlib import Path

from sfapi_client import Client
from sfapi_client.jobs import JobState


def test_compute(client_id, client_secret, test_machine):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        assert machine.status in ["active", "unavailable", "degraded", "other"]
        assert machine.name == test_machine.value


def test_job(client_id, client_secret, test_job_path, test_machine):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)

        job = machine.submit_job(test_job_path)
        job.complete()
        assert job.state == JobState.COMPLETED

        job_looked_up = machine.job(job.jobid)

        assert job.jobid == job_looked_up.jobid


def test_fetch_jobs(client_id, client_secret, test_machine, test_username):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        machine.jobs(user=test_username)


def test_list_dir_contents(client_id, client_secret, test_machine, test_job_path):
    with Client(client_id, client_secret) as client:
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


def test_list_dir(client_id, client_secret, test_machine, test_job_path):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        test_job = Path(test_job_path)
        test_path = test_job.parent

        paths = machine.ls(test_path, directory=True)
        assert len(paths) == 1
        assert paths[0].name == test_path.name


def test_list_file(client_id, client_secret, test_machine, test_job_path):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        test_job_filename = Path(test_job_path).name

        paths = machine.ls(test_job_path)

        found = False
        for p in paths:
            if p.name == test_job_filename:
                found = True
                break

        assert found


def test_run_arg_list(client_id, client_secret, test_machine, test_job_path):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        output = machine.run(["ls", test_job_path])

        assert test_job_path in output


def test_run_arg_str(client_id, client_secret, test_machine, test_job_path):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        output = machine.run(f"ls {test_job_path}")

        assert test_job_path in output


def test_run_arg_path(client_id, client_secret, test_machine):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        [remote_path] = machine.ls("/usr/bin/hostname")
        output = machine.run(remote_path)

        assert output
