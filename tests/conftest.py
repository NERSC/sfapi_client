import os
import json
import random
import string
from typing import Optional, Union, Dict

import pytest
from authlib.jose import JsonWebKey

from sfapi_client.compute import Machine
from sfapi_client import Resource

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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
