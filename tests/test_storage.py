from time import sleep
from io import BytesIO
import random


def test_transfer_file(authenticated_client, test_machine, test_tmp_dir):
    # Takes a lot from test_upload_file_to_file to prepare a file at NERSC
    # Then moves the file with Globus and reads the new file
    with authenticated_client as client:
        pytest_num = random.randint(0, 100)
        machine = client.compute(test_machine)
        paths = machine.ls(test_tmp_dir, directory=True)
        assert len(paths) == 1
        [tmp] = paths

        # Create empty file
        _file = BytesIO()
        _file.filename = "hello.txt"
        remote_file = tmp.upload(_file)

        # Now upload to the file
        file_contents = "test globus transfer"
        remote_file = remote_file.upload(BytesIO(file_contents.encode()))

        transfered_file = f"{test_tmp_dir}/output_{pytest_num}"
        result = client.storage.globus.start_transfer(
            "dtn", "dtn", remote_file, transfered_file, f"pytest client {pytest_num}"
        )
        transfer_id = result.transfer_id

        # Wait for ~minute
        for _ in range(6):
            out = client.storage.globus.check_transfer(transfer_id)
            if out.globus_status == "SUCCEEDED":
                break
            sleep(10)

        # Download the transfered file and check it made it there
        [transfered_file] = machine.ls(transfered_file)
        assert (transfered_file.download()).read() == file_contents
