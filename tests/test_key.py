import pytest

from sfapi_client import Client
from sfapi_client.exceptions import ClientKeyError


@pytest.mark.public
def test_wrong_key_data(fake_key_file, test_machine):
    with Client(key=fake_key_file) as client:
        with pytest.raises(Exception):
            # Raises OAuthError when trying to read incorrect PEM
            client.compute(test_machine)


@pytest.mark.public
def test_empty_key_file(empty_key_file):
    with pytest.raises(ClientKeyError):
        # Raise ClientKeyError for emtpy key file
        Client(key=empty_key_file)


@pytest.mark.public
def test_no_key_file_path():
    with pytest.raises(ClientKeyError):
        # Raise error when there is no key present
        Client(key="~/name")


@pytest.mark.public
def test_no_key_file_name():
    with pytest.raises(ClientKeyError):
        # Raise error when searching for keys
        Client(key="name")
