import pytest

from sfapi_client import SfApiError, Client


@pytest.mark.public
def test_no_creds(unauthenticated_client):
    with unauthenticated_client as client:
        assert client is not None


@pytest.mark.public
def test_no_creds_auth_required(unauthenticated_client, test_machine):
    with unauthenticated_client as client:
        machine = client.compute(test_machine)
        with pytest.raises(SfApiError):
            machine.jobs()


def test_access_token(api_base_url, access_token, test_machine, test_username):
    with Client(api_base_url=api_base_url, access_token=access_token) as client:
        machine = client.compute(test_machine)
        machine.jobs(user=test_username)
