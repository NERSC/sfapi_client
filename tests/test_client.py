import pytest

from sfapi_client import SfApiError


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
