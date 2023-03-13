import pytest
from pathlib import Path

from sfapi_client import AsyncClient
from sfapi_client._async.path import RemotePath


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
