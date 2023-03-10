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


def test_download_text(client_id, client_secret, test_machine, test_job_path):
    with Client(client_id, client_secret) as client:
        machine = client.compute(test_machine)
        test_job = Path(test_job_path)
        test_path = test_job.parent
        test_name = test_job.name

        paths = machine.listdir(test_path)

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

        paths = machine.listdir(test_path)

        remote_path = None
        for p in paths:
            if p.name == test_name:
                remote_path = p
                break

        assert remote_path is not None

        fp = remote_path.download(binary=True)
        bytes = fp.read()
        assert "#SBATCH" in bytes.decode()
