import pytest
from io import BytesIO
import random


@pytest.mark.asyncio
async def test_transfer_file(async_authenticated_client, test_machine, test_tmp_dir):
    # Takes a lot from test_upload_file_to_file to prepare a file at NERSC
    # Then moves the file with Globus and reads the new file
    async with async_authenticated_client as client:
        pytest_num = random.randint(0, 100)
        machine = await client.compute(test_machine)
        paths = await machine.ls(test_tmp_dir, directory=True)
        assert len(paths) == 1
        [tmp] = paths

        # Create empty file
        _file = BytesIO()
        _file.filename = "hello.txt"
        remote_file = await tmp.upload(_file)

        # Now upload to the file
        file_contents = "test globus transfer"
        remote_file = await remote_file.upload(BytesIO(file_contents.encode()))

        transfered_file = f"{test_tmp_dir}/output_{pytest_num}"
        globus_client = await client.storage.globus()

        globus_resp = await globus_client.start_transfer(
            test_machine,
            test_machine,
            remote_file,
            transfered_file,
            f"pytest async client {pytest_num}",
        )

        await globus_resp.complete()

        globus_check_back = await globus_client.transfer(globus_resp.transfer_id)

        assert globus_check_back.transfer_id == globus_resp.transfer_id
        assert globus_check_back.globus_status == "SUCCEEDED"

        # Download the transfered file and check it made it there
        [transfered_file] = await machine.ls(transfered_file)
        assert (await transfered_file.download()).read() == file_contents
