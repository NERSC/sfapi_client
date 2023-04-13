import pytest
from pathlib import Path
from io import BytesIO
import random
import string

from sfapi_client import AsyncClient
from sfapi_client.paths import AsyncRemotePath


@pytest.mark.asyncio
async def test_download_text(client_id, client_secret, test_machine, test_job_path):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        test_job = Path(test_job_path)
        test_path = test_job.parent
        test_name = test_job.name

        paths = await machine.ls(test_path)

        remote_path = None
        for p in paths:
            if p.name == test_name:
                remote_path = p
                break

        assert remote_path is not None

        fp = await remote_path.download()
        contents = fp.read()
        assert "#SBATCH" in contents


@pytest.mark.asyncio
async def test_download_binary(client_id, client_secret, test_machine, test_job_path):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        test_job = Path(test_job_path)
        test_path = test_job.parent
        test_name = test_job.name

        paths = await machine.ls(test_path)

        remote_path = None
        for p in paths:
            if p.name == test_name:
                remote_path = p
                break

        assert remote_path is not None

        fp = await remote_path.download(binary=True)
        bytes = fp.read()
        assert "#SBATCH" in bytes.decode()


@pytest.mark.asyncio
async def test_download_directory(
    client_id, client_secret, test_machine, test_job_path
):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        test_job = Path(test_job_path)
        test_path = test_job.parent.parent
        test_name = test_job.name

        paths = await machine.ls(test_path)

        remote_path = None
        for p in paths:
            if p.name == test_job.parent.name:
                remote_path = p
                break

        with pytest.raises(IsADirectoryError):
            await remote_path.download()


@pytest.mark.asyncio
async def test_ls_dir(
    client_id, client_secret, test_machine, test_job_path, test_username
):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        test_job = Path(test_job_path)
        test_job_directory_name = test_job.parent.name
        test_job_filename = test_job.name
        test_job_parent_directory = test_job.parent.parent

        paths = await machine.ls(test_job_parent_directory)

        test_job_directory = None
        for p in paths:
            if p.name == test_job_directory_name:
                test_job_directory = p
                break

        assert test_job_directory is not None

        # Now list the job path an assert the at we can find the test job
        found = False
        job_path_entries = await test_job_directory.ls()
        for p in job_path_entries:
            if p.name == test_job_filename:
                found = True
                break

        assert found


@pytest.mark.asyncio
async def test_ls_excludes_dots(client_id, client_secret, test_machine, test_job_path):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        test_job = Path(test_job_path)
        test_job_directory = test_job.parent

        paths = await machine.ls(test_job_directory)

        dots = False

        for p in paths:
            if p.name in [".", ".."]:
                dots = True

        assert not dots


@pytest.mark.asyncio
async def test_upload_file_to_directory(
    client_id, client_secret, test_machine, test_tmp_dir
):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)

        paths = await machine.ls(test_tmp_dir, directory=True)
        assert len(paths) == 1
        [tmp] = paths

        file_contents = "hello world!"
        file = BytesIO(file_contents.encode())
        file.filename = "hello.txt"
        remote_file = await tmp.upload(file)

        assert (await remote_file.download()).read() == file_contents


@pytest.mark.asyncio
async def test_upload_file_to_file(
    client_id, client_secret, test_machine, test_tmp_dir
):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)

        paths = await machine.ls(test_tmp_dir, directory=True)
        assert len(paths) == 1
        [tmp] = paths

        # Create empty file
        file = BytesIO()
        file.filename = "hello.txt"
        remote_file = await tmp.upload(file)

        # Now upload to the file
        file_contents = "goodbye world!"
        remote_file = await remote_file.upload(BytesIO(file_contents.encode()))

        assert (await remote_file.download()).read() == file_contents


@pytest.mark.asyncio
async def test_file_open_invalid_mode(
    client_id, client_secret, test_machine, test_job_path
):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        [test_job_remote_path] = await machine.ls(test_job_path)

        with pytest.raises(ValueError):
            async with test_job_remote_path.open("dse") as fp:
                pass

        with pytest.raises(ValueError):
            async with test_job_remote_path.open("rr") as fp:
                pass

        with pytest.raises(ValueError):
            async with test_job_remote_path.open("ww") as fp:
                pass

        with pytest.raises(ValueError):
            async with test_job_remote_path.open("wr") as fp:
                pass


@pytest.mark.asyncio
async def test_file_open_read_text(
    client_id, client_secret, test_machine, test_job_path
):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        test_job_remote_path = await machine.ls(test_job_path)
        assert len(test_job_remote_path) == 1
        [path] = test_job_remote_path

        async with path.open("r") as fp:
            contents = fp.read()
            assert "#SBATCH" in contents


@pytest.mark.asyncio
async def test_file_open_read_binary(
    client_id, client_secret, test_machine, test_job_path
):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        test_job_remote_path = await machine.ls(test_job_path)
        assert len(test_job_remote_path) == 1
        [path] = test_job_remote_path

        async with path.open("br") as fp:
            contents = fp.read().decode()
            assert "#SBATCH" in contents


@pytest.mark.asyncio
async def test_file_open_write_text(
    client_id, client_secret, test_machine, test_tmp_dir
):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        remote_tmp_dir = await machine.ls(test_tmp_dir, directory=True)
        assert len(remote_tmp_dir) == 1
        [tmp_dir] = remote_tmp_dir

        # Create empty file
        file = BytesIO()
        file.filename = "hello.txt"
        remote_file = await tmp_dir.upload(file)

        # Now write to the file
        file_contents = "hi"
        async with remote_file.open("w") as fp:
            fp.write(file_contents)

        # Now check that the content has changed
        async with remote_file.open("r") as fp:
            assert file_contents in fp.read()


@pytest.mark.asyncio
async def test_file_open_write_binary(
    client_id, client_secret, test_machine, test_tmp_dir
):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        remote_tmp_dir = await machine.ls(test_tmp_dir, directory=True)
        assert len(remote_tmp_dir) == 1
        [tmp_dir] = remote_tmp_dir

        # Create empty file
        file = BytesIO()
        file.filename = "hello.txt"
        remote_file = await tmp_dir.upload(file)

        # Now write to the file
        file_contents = "hi"
        async with remote_file.open("wb") as fp:
            fp.write(file_contents.encode())

        # Now check that the content has changed
        async with remote_file.open("r") as fp:
            assert file_contents in fp.read()


@pytest.mark.asyncio
async def test_file_open_write_new(
    client_id, client_secret, test_machine, test_tmp_dir
):
    async with AsyncClient(client_id, client_secret) as client:
        machine = await client.compute(test_machine)
        remote_tmp_dir = await machine.ls(test_tmp_dir, directory=True)
        assert len(remote_tmp_dir) == 1
        [tmp_dir] = remote_tmp_dir

        # Create empty file
        random_name = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=10)
        )
        remote_file = tmp_dir / f"{random_name}.txt"

        # Now write to the file
        file_contents = "hi"
        async with remote_file.open("wb") as fp:
            fp.write(file_contents.encode())

        # Now check that the content has changed
        async with remote_file.open("r") as fp:
            assert file_contents in fp.read()
