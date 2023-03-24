import pytest

from sfapi_client import Client
from sfapi_client import JobState
from sfapi_client import Machines


def test_submit(client_id, client_secret, test_job_path, test_machine):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        job = machine.submit_job(test_job_path)

        state = job.complete()

        assert state == JobState.COMPLETED


def test_cancel(client_id, client_secret, test_job_path, test_machine):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        job = machine.submit_job(test_job_path)

        job.cancel()


def test_cancel_wait_for_it(client_id, client_secret, test_job_path, test_machine):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        job = machine.submit_job(test_job_path)
        job.cancel(wait=True)


def test_running(client_id, client_secret, test_job_path, test_machine):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        job = machine.submit_job(test_job_path)

        state = job.running()

        assert state == JobState.RUNNING


def test_running_timeout(client_id, client_secret, test_job_path, test_machine):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        job = machine.submit_job(test_job_path)

        with pytest.raises(TimeoutError):
            job.running(timeout=10)


def test_complete_timeout(client_id, client_secret, test_job_path, test_machine):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        job = machine.submit_job(test_job_path)

        with pytest.raises(TimeoutError):
            job.complete(timeout=10)
