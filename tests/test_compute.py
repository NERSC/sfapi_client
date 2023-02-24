import pytest

from sfapi_client import Client
from sfapi_client import JobState
from sfapi_client import Machines


def test_compute(client_id, client_secret):
    with Client(client_id, client_secret) as client:
        perl = client.compute(Machines.perlmutter)

        assert perl.name == Machines.perlmutter.value


def test_job(client_id, client_secret, test_job_path):
    with Client(client_id, client_secret) as client:
        perl = client.compute(Machines.perlmutter)

        job = perl.submit_job(test_job_path)
        job.complete()
        assert job.state == JobState.COMPLETED

        perl_job = perl.job(job.jobid)

        assert perl_job.jobid == job.jobid
