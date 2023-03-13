import pytest
from pathlib import Path

from sfapi_client import Client
from sfapi_client._async.path import RemotePath


def test_concat():
    a = RemotePath("/a")
    b = RemotePath("b")
    c = "c"

    new_path = a / b
    assert isinstance(new_path, RemotePath)
    assert new_path.name == "b"
    assert new_path.group is None
    assert str(new_path) == "/a/b"

    new_path = c / b
    assert isinstance(new_path, RemotePath)
    assert new_path.name == "b"
    assert new_path.group is None
    assert str(new_path) == "c/b"


def test_parent():
    test_path = RemotePath("/foo")
    assert isinstance(test_path.parent, RemotePath)
    for p in test_path.parents:
        assert isinstance(p, RemotePath)


def test_download_text(client_id, client_secret, test_machine, test_job_path):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        test_job = Path(test_job_path)
        test_path = test_job.parent
        test_name = test_job.name

        paths = machine.ls(test_path)

        remote_path = None
        for p in paths:
            if p.name == test_name:
                remote_path = p
                break

        assert remote_path is not None

        fp = remote_path.download()
        contents = fp.read()
        assert "#SBATCH" in contents


def test_download_binary(client_id, client_secret, test_machine, test_job_path):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        test_job = Path(test_job_path)
        test_path = test_job.parent
        test_name = test_job.name

        paths = machine.ls(test_path)

        remote_path = None
        for p in paths:
            if p.name == test_name:
                remote_path = p
                break

        assert remote_path is not None

        fp = remote_path.download(binary=True)
        bytes = fp.read()
        assert "#SBATCH" in bytes.decode()


def test_ls_dir(client_id, client_secret, test_machine, test_job_path, test_username):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        test_job = Path(test_job_path)
        test_job_directory_name = test_job.parent.name
        test_job_filename = test_job.name
        test_job_parent_directory = test_job.parent.parent

        paths = machine.ls(test_job_parent_directory)

        test_job_directory = None
        for p in paths:
            if p.name == test_job_directory_name:
                test_job_directory = p
                break

        assert test_job_directory is not None

        # Now list the job path an assert the at we can find the test job
        found = False
        job_path_entries = test_job_directory.ls()
        for p in job_path_entries:
            if p.name == test_job_filename:
                found = True
                break

        assert found
