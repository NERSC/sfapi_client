import pytest

from sfapi_client import Client
from sfapi_client import JobState
from sfapi_client import Machines


def test_compute(client_id, client_secret, test_machine):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)

        assert machine.name == test_machine.value


def test_job(client_id, client_secret, test_job_path, test_machine):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)

        job = machine.submit_job(test_job_path)
        job.complete()
        assert job.state == JobState.COMPLETED

        job_looked_up = machine.job(job.jobid)

        assert job.jobid == job_looked_up.jobid
