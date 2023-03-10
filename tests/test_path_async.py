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

        paths = await machine.listdir(test_path)

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

        paths = await machine.listdir(test_path)

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
        test_path = test_job.parent
        test_name = test_job.name

        paths = await machine.listdir(test_path)

        remote_path = None
        for p in paths:
            if p.name == ".":
                remote_path = p
                break

        with pytest.raises(IsADirectoryError):
            await remote_path.download()
