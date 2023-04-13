import pytest
from concurrent.futures import ThreadPoolExecutor
import time

from sfapi_client import Client
from sfapi_client.jobs import JobState
from sfapi_client.compute import Compute
from sfapi_client.jobs import JobSqueue


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
    with Client(client_id, client_secret, wait_interval=1) as client:
        machine = client.compute(test_machine)
        job = machine.submit_job(test_job_path)

        state = job.running()

        assert state == JobState.RUNNING


def test_running_timeout(client_id, client_secret, test_job_path, test_machine):
    with Client(client_id, client_secret, wait_interval=1) as client:
        machine = client.compute(test_machine)
        job = machine.submit_job(test_job_path)

        with pytest.raises(TimeoutError):
            job.running(timeout=1)


def test_complete_timeout(client_id, client_secret, test_job_path, test_machine):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        job = machine.submit_job(test_job_path)

        with pytest.raises(TimeoutError):
            job.complete(timeout=10)


def test_job_monitor_check_request(
    mocker,
    client_id,
    client_secret,
    test_job_path,
    test_machine,
    dev_api_url,
):
    with Client(client_id, client_secret, api_base_url=dev_api_url) as client:
        num_jobs = 10
        _fetch_jobs = mocker.patch("sfapi_client._monitor._fetch_jobs")

        machine = client.compute(test_machine)

        # Create some test jobs for mocking
        test_jobs = [JobSqueue(jobid=i) for i in range(0, num_jobs)]
        for j in test_jobs:
            j.compute = machine

        # Patch the submit_job to return the test jobs
        submit_job = mocker.patch.object(Compute, "submit_job")
        submit_job.side_effect = test_jobs

        # Patch the return value of _fetch_jobs_async to return
        # the test jobs
        _fetch_jobs.return_value = test_jobs

        def _jobs(*arg, **kwargs):
            time.sleep(1)

            return test_jobs

        _fetch_jobs.side_effect = _jobs

        # Submit a bunch on jobs
        jobs = []
        for _ in range(0, num_jobs):
            jobs.append(machine.submit_job(test_job_path))

        # Run update on all jobs in multiple threads
        futures = []
        with ThreadPoolExecutor(max_workers=num_jobs) as executor:
            for j in jobs:
                futures.append(executor.submit(j.update))

            executor.shutdown(wait=True)

        for f in futures:
            assert f.exception() is None

        # We should have less requests than the number of jobs
        assert _fetch_jobs.call_count < num_jobs

        # Check that the state of all jobs have been requested
        calls = _fetch_jobs.call_args_list

        ids = set()
        for _, kwargs in calls:
            ids.update(kwargs["jobids"])

        assert len(ids) == num_jobs


# We currently run this in api-dev as its a new feature deployed there
def test_job_monitor_multiple_threads(
    client_id, client_secret, test_job_path, test_machine, dev_api_url
):
    num_jobs = 5

    with Client(client_id, client_secret, api_base_url=dev_api_url) as client:
        machine = client.compute(test_machine)

        jobs = []

        def _submit_job():
            job = machine.submit_job(test_job_path)
            jobs.append(job)
            job.complete()

        futures = []
        with ThreadPoolExecutor(max_workers=num_jobs) as executor:
            for _ in range(0, num_jobs):
                futures.append(executor.submit(_submit_job))

            executor.shutdown(wait=True)

        for f in futures:
            assert f.exception() is None

        for j in jobs:
            assert j.state == JobState.COMPLETED
