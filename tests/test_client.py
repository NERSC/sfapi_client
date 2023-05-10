import pytest
import httpx

from sfapi_client import Client


@pytest.mark.public
def test_no_creds():
    with Client() as client:
        assert client is not None


@pytest.mark.public
def test_no_creds_auth_required(test_machine):
    with Client() as client:
        machine = client.compute(test_machine)
        with pytest.raises(httpx.HTTPStatusError):
            machine.jobs()
