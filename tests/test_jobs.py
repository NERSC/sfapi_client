import pytest

from sfapi_client import Client
from sfapi_client import JobState
from sfapi_client import Machines


def test_submit(client_id, client_secret, test_job_path):
    with Client(client_id, client_secret) as client:
        perl = client.compute(Machines.perlmutter)
        job = perl.submit_job(test_job_path)

        job.complete()

        assert job.state == JobState.COMPLETED


def test_cancel(client_id, client_secret, test_job_path):
    with Client(client_id, client_secret) as client:
        perl = client.compute(Machines.perlmutter)
        job = perl.submit_job(test_job_path)

        job.cancel()


def test_cancel_wait_for_it(client_id, client_secret, test_job_path):
    with Client(client_id, client_secret) as client:
        perl = client.compute(Machines.perlmutter)
        job = perl.submit_job(test_job_path)
        job.cancel(wait=True)

        assert job.state == JobState.CANCELLED
