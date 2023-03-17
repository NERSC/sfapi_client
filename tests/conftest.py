import os
import json

import pytest
from authlib.jose import JsonWebKey

from sfapi_client import Machines


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


TEST_MACHINE_ENV = "TEST_MACHINE"


@pytest.fixture
def test_machine():
    if TEST_MACHINE_ENV in os.environ:
        return Machines[os.environ[TEST_MACHINE_ENV]]
    else:
        return Machines.perlmutter


@pytest.fixture
def test_username():
    return os.environ["TEST_USERNAME"]


@pytest.fixture
def test_file_contents():
    return "hello world"


@pytest.fixture
def test_tmp_dir():
    return os.environ["TEST_TMP_DIR"]


@pytest.fixture
def test_group():
    return os.environ["TEST_GROUP"]


@pytest.fixture
def test_project():
    return os.environ["TEST_PROJECT"]


@pytest.fixture
def test_group_create():
    return os.environ["TEST_GROUP_CREATE"]
