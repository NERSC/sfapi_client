from __future__ import annotations
from typing import Dict, Any, Optional
from pathlib import Path

from authlib.integrations.httpx_client.oauth2_client import OAuth2Client
from authlib.oauth2.rfc7523 import PrivateKeyJWT
import httpx
import tenacity

from .compute import Machines, Compute
from .common import SfApiError
from .._models import (
    JobOutput as JobStatusResponse,
    UserInfo as User,
    AppRoutersComputeModelsStatus as JobStatus,
)

SFAPI_TOKEN_URL = "https://oidc.nersc.gov/c2id/token"
SFAPI_BASE_URL = "https://api.nersc.gov/api/v1.2"


class Client:
    def __init__(
        self,
        client_id: Optional[str] = None,
        secret: Optional[str] = None,
        key_name: Optional[str] = None,
    ):
        if any(arg is None for arg in (client_id, secret)):
            self._get_client_secret_from_file(key_name)
        else:
            self._client_id = client_id
            self._secret = secret
        self._oauth2_session = None

    def __enter__(self):
        self._oauth2_session = OAuth2Client(
            client_id=self._client_id,
            client_secret=self._secret,
            token_endpoint_auth_method=PrivateKeyJWT(SFAPI_TOKEN_URL),
            grant_type="client_credentials",
            token_endpoint=SFAPI_TOKEN_URL,
            timeout=10.0,
        )

        self._oauth2_session.fetch_token()

        return self

    def __exit__(self, type, value, traceback):
        if self._oauth2_session is not None:
            self._oauth2_session.close()

    def _get_client_secret_from_file(self, name):
        if name is not None and Path(name).exists():
            # If the user gives a full path, then use it
            key_path = Path(name)
        else:
            # If not let's search in ~/.superfacility for the name or any key
            nickname = "" if name is None else name
            keys = Path().home() / ".superfacility"
            key_paths = list(keys.glob(f"{nickname}*"))
            if len(key_paths) == 0:
                raise SfApiError(
                    f"No keys found in search of ~/.superfacility/{nickname}*"
                )
            key_path = Path(key_paths[0])

        # Make key read only in case it's not
        key_path.chmod(0o600)

        # get the client_id from the name
        self._client_id = key_path.stem.split("-")[-1]
        # Read the secret from the file
        with open(Path(key_path)) as secret:
            self._secret = secret.read()
        return True

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(httpx.TimeoutException)
        | tenacity.retry_if_exception_type(httpx.ConnectError)
        | tenacity.retry_if_exception_type(httpx.HTTPStatusError),
        wait=tenacity.wait_exponential(max=10),
        stop=tenacity.stop_after_attempt(10),
    )
    def get(self, url: str, params: Dict[str, Any] = {}) -> httpx.Response:
        self._oauth2_session.ensure_active_token(self._oauth2_session.token)

        r = self._oauth2_session.get(
            f"{SFAPI_BASE_URL}/{url}",
            headers={
                "Authorization": self._oauth2_session.token["access_token"],
                "accept": "application/json",
            },
            params=params,
        )
        r.raise_for_status()

        return r

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(httpx.TimeoutException)
        | tenacity.retry_if_exception_type(httpx.ConnectError)
        | tenacity.retry_if_exception_type(httpx.HTTPStatusError),
        wait=tenacity.wait_exponential(max=10),
        stop=tenacity.stop_after_attempt(10),
    )
    def post(self, url: str, data: Dict[str, Any]) -> httpx.Response:
        self._oauth2_session.ensure_active_token(self._oauth2_session.token)

        r = self._oauth2_session.post(
            f"{SFAPI_BASE_URL}/{url}",
            headers={
                "Authorization": self._oauth2_session.token["access_token"],
                "accept": "application/json",
            },
            data=data,
        )
        r.raise_for_status()

        return r

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(httpx.TimeoutException)
        | tenacity.retry_if_exception_type(httpx.ConnectError)
        | tenacity.retry_if_exception_type(httpx.HTTPStatusError),
        wait=tenacity.wait_exponential(max=10),
        stop=tenacity.stop_after_attempt(10),
    )
    def delete(self, url: str) -> httpx.Response:
        self._oauth2_session.ensure_active_token(self._oauth2_session.token)

        r = self._oauth2_session.delete(
            f"{SFAPI_BASE_URL}/{url}",
            headers={
                "Authorization": self._oauth2_session.token["access_token"],
                "accept": "application/json",
            },
        )
        r.raise_for_status()

        return r

    def compute(self, machine: Machines) -> Compute:
        response = self.get(f"status/{machine.value}")

        compute = Compute.parse_obj(response.json())
        compute.client = self

        return compute

    def user(self, username: Optional[str] = None) -> User:
        params = {}
        if username is not None:
            params["username"] = username

        response = self.get("account/", params)
        json_response = response.json()

        return User.parse_obj(json_response)
