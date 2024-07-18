import pytest
from pathlib import Path
from io import BytesIO
import random
import string

from sfapi_client.paths import RemotePath


def test_concat():
    a = RemotePath("/a", compute=None)
    b = RemotePath("b", compute=None)
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
    test_path = RemotePath("/foo", compute=None)
    assert isinstance(test_path.parent, RemotePath)
    for p in test_path.parents:
        assert isinstance(p, RemotePath)


def test_download_text(authenticated_client, test_machine, test_job_path):
    with authenticated_client as client:
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


def test_download_binary(authenticated_client, test_machine, test_job_path):
    with authenticated_client as client:
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


def test_ls_dir(authenticated_client, test_machine, test_job_path, test_username):
    with authenticated_client as client:
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


def test_upload_file_to_directory(authenticated_client, test_machine, test_tmp_dir):
    with authenticated_client as client:
        machine = client.compute(test_machine)

        paths = machine.ls(test_tmp_dir, directory=True)
        assert len(paths) == 1
        [tmp] = paths

        file_contents = "hello world!"
        file = BytesIO(file_contents.encode())
        file.filename = "hello.txt"
        remote_file = tmp.upload(file)

        assert remote_file.download().read() == file_contents


def test_upload_file_to_file(authenticated_client, test_machine, test_tmp_dir):
    with authenticated_client as client:
        machine = client.compute(test_machine)

        paths = machine.ls(test_tmp_dir, directory=True)
        assert len(paths) == 1
        [tmp] = paths

        # Create empty file
        file = BytesIO()
        file.filename = "hello.txt"
        remote_file = tmp.upload(file)

        # Now upload to the file
        file_contents = "goodbye world!"
        remote_file = remote_file.upload(BytesIO(file_contents.encode()))

        assert remote_file.download().read() == file_contents


def test_file_open_invalid_mode(authenticated_client, test_machine, test_job_path):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        [test_job_remote_path] = machine.ls(test_job_path)

        with pytest.raises(ValueError):
            with test_job_remote_path.open("dse"):
                pass

        with pytest.raises(ValueError):
            with test_job_remote_path.open("rr"):
                pass

        with pytest.raises(ValueError):
            with test_job_remote_path.open("ww"):
                pass

        with pytest.raises(ValueError):
            with test_job_remote_path.open("wr"):
                pass


def test_file_open_read_text(authenticated_client, test_machine, test_job_path):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        test_job_remote_path = machine.ls(test_job_path)
        assert len(test_job_remote_path) == 1
        [path] = test_job_remote_path

        with path.open("r") as fp:
            contents = fp.read()
            assert "#SBATCH" in contents


def test_file_open_read_binary(authenticated_client, test_machine, test_job_path):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        test_job_remote_path = machine.ls(test_job_path)
        assert len(test_job_remote_path) == 1
        [path] = test_job_remote_path

        with path.open("br") as fp:
            contents = fp.read().decode()
            assert "#SBATCH" in contents


def test_file_open_write_text(authenticated_client, test_machine, test_tmp_dir):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        remote_tmp_dir = machine.ls(test_tmp_dir, directory=True)
        assert len(remote_tmp_dir) == 1
        [tmp_dir] = remote_tmp_dir

        # Create empty file
        file = BytesIO()
        file.filename = "hello.txt"
        remote_file = tmp_dir.upload(file)

        # Now write to the file
        file_contents = "hi"
        with remote_file.open("w") as fp:
            fp.write(file_contents)

        # Now check that the content has changed
        with remote_file.open("r") as fp:
            assert file_contents in fp.read()


def test_file_open_write_binary(authenticated_client, test_machine, test_tmp_dir):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        remote_tmp_dir = machine.ls(test_tmp_dir, directory=True)
        assert len(remote_tmp_dir) == 1
        [tmp_dir] = remote_tmp_dir

        # Create empty file
        file = BytesIO()
        file.filename = "hello.txt"
        remote_file = tmp_dir.upload(file)

        # Now write to the file
        file_contents = "hi"
        with remote_file.open("wb") as fp:
            fp.write(file_contents.encode())

        # Now check that the content has changed
        with remote_file.open("r") as fp:
            assert file_contents in fp.read()


def test_file_open_write_new(authenticated_client, test_machine, test_tmp_dir):
    with authenticated_client as client:
        machine = client.compute(test_machine)
        remote_tmp_dir = machine.ls(test_tmp_dir, directory=True)
        assert len(remote_tmp_dir) == 1
        [tmp_dir] = remote_tmp_dir

        # Create empty file
        random_name = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=10)
        )
        remote_file = tmp_dir / f"{random_name}.txt"

        # Now write to the file
        file_contents = "hi"
        with remote_file.open("wb") as fp:
            fp.write(file_contents.encode())

        # Now check that the content has changed
        with remote_file.open("r") as fp:
            assert file_contents in fp.read()
