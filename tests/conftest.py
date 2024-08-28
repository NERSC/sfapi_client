import json
import random
import string
from typing import Optional, Union, Dict
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa

import pytest
from authlib.jose import JsonWebKey

from sfapi_client.compute import Machine
from sfapi_client import Resource
from sfapi_client import Client, AsyncClient

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_BASE_URL: str = "https://api.nersc.gov/api/v1.2"
    TOKEN_URL: str = "https://oidc.nersc.gov/c2id/token"
    SFAPI_CLIENT_ID: Optional[str] = None
    SFAPI_CLIENT_SECRET: Optional[Union[str, Dict]] = None
    SFAPI_DEV_CLIENT_ID: Optional[str] = None
    SFAPI_DEV_CLIENT_SECRET: Optional[Union[str, Dict]] = None
    TEST_JOB_PATH: Optional[str] = None
    TEST_MACHINE: Machine = Machine.perlmutter
    TEST_RESOURCE: Resource = Resource.spin
    TEST_USERNAME: Optional[str] = None
    TEST_ANOTHER_USERNAME: Optional[str] = None
    TEST_TMP_DIR: Optional[str] = None
    TEST_PROJECT: Optional[str] = None
    TEST_GROUP: Optional[str] = None
    DEV_API_URL: str = "https://api-dev.nersc.gov/api/v1.2"
    DEV_TOKEN_URL: str = "https://oidc-dev.nersc.gov/c2id/token"
    ACCESS_TOKEN: Optional[str] = None

    model_config = ConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()


@pytest.fixture
def client_id():
    return settings.SFAPI_CLIENT_ID


@pytest.fixture
def client_secret():
    json_web_key = settings.SFAPI_CLIENT_SECRET

    if isinstance(json_web_key, str):
        json_web_key = json.loads(json_web_key)

    return JsonWebKey.import_key(json_web_key)


@pytest.fixture
def dev_client_id():
    return settings.SFAPI_DEV_CLIENT_ID


@pytest.fixture
def dev_client_secret():
    json_web_key = settings.SFAPI_DEV_CLIENT_SECRET

    if isinstance(json_web_key, str):
        json_web_key = json.loads(json_web_key)

    return JsonWebKey.import_key(json_web_key)


@pytest.fixture
def test_job_path():
    return settings.TEST_JOB_PATH


@pytest.fixture
def test_machine():
    return settings.TEST_MACHINE


@pytest.fixture
def test_resource():
    return settings.TEST_RESOURCE


@pytest.fixture
def test_username():
    return settings.TEST_USERNAME


@pytest.fixture
def test_another_username():
    return settings.TEST_ANOTHER_USERNAME


@pytest.fixture
def test_file_contents():
    return "hello world"


@pytest.fixture
def test_tmp_dir():
    return settings.TEST_TMP_DIR


@pytest.fixture
def test_group():
    return settings.TEST_GROUP


@pytest.fixture
def test_random_group():
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

    return f"t-{rand}"


@pytest.fixture
def test_project():
    return settings.TEST_PROJECT


@pytest.fixture
def dev_api_url():
    return settings.DEV_API_URL


@pytest.fixture
def dev_token_url():
    return settings.DEV_TOKEN_URL


@pytest.fixture
def api_base_url():
    return settings.API_BASE_URL


@pytest.fixture
def token_url():
    return settings.TOKEN_URL


@pytest.fixture
def unauthenticated_client(api_base_url):
    return Client(api_base_url=api_base_url)


@pytest.fixture
def async_unauthenticated_client(api_base_url):
    return AsyncClient(api_base_url=api_base_url)


@pytest.fixture
def authenticated_client(api_base_url, token_url, client_id, client_secret):
    return Client(
        api_base_url=api_base_url,
        token_url=token_url,
        client_id=client_id,
        secret=client_secret,
    )


@pytest.fixture
def async_authenticated_client(api_base_url, token_url, client_id, client_secret):
    return AsyncClient(
        api_base_url=api_base_url,
        token_url=token_url,
        client_id=client_id,
        secret=client_secret,
    )


@pytest.fixture
def access_token():
    return settings.ACCESS_TOKEN


@pytest.fixture
def fake_key_file(tmp_path_factory):
    try:
        tmp_path_factory._basetemp = Path().home()
        key_path = tmp_path_factory.mktemp(".sfapi_test1", numbered=False) / "key.pem"

        # Make a fake key for testing
        key_path.write_text(
            f"""abcdefghijlmo
    -----BEGIN RSA PRIVATE KEY-----
    {rsa.generate_private_key(public_exponent=65537, key_size=2048)}
    -----END RSA PRIVATE KEY-----
    """
        )
        key_path.chmod(0o100600)
        yield key_path
    finally:
        # make sure to cleanup the test since we put a file in ~/.sfapi_test
        temp_path = Path().home() / ".sfapi_test1"
        if temp_path.exists():
            (temp_path / "key.pem").unlink(missing_ok=True)
            temp_path.rmdir()


@pytest.fixture
def empty_key_file(tmp_path_factory):
    try:
        tmp_path_factory._basetemp = Path().home()
        key_path = tmp_path_factory.mktemp(".sfapi_test2", numbered=False) / "nokey.pem"
        # Makes an empty key
        key_path.write_text("")
        key_path.chmod(0o100600)
        yield key_path
    finally:
        # make sure to cleanup the test since we put a file in ~/.sfapi_test
        temp_path = Path().home() / ".sfapi_test2"
        if temp_path.exists():
            (temp_path / "nokey.pem").unlink(missing_ok=True)
            temp_path.rmdir()
