import os
import json

import pytest
from authlib.jose import JsonWebKey


@pytest.fixture
def client_id():
    return os.environ["SFAPI_CLIENT_ID"]


@pytest.fixture
def client_secret():
    json_web_key = os.environ["SFAPI_CLIENT_SECRET"]

    return JsonWebKey.import_key(json.loads(json_web_key))


@pytest.fixture
def test_job_path():
    return os.environ["TEST_JOB_PATH"]
