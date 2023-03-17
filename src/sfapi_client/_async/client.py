from __future__ import annotations
from typing import Dict, Any, Optional
from pathlib import Path
import json

from authlib.integrations.httpx_client.oauth2_client import AsyncOAuth2Client
from authlib.oauth2.rfc7523 import PrivateKeyJWT
import httpx
import tenacity
from authlib.jose import JsonWebKey

from .compute import Machines, Compute
from .common import SfApiError
from .._models import (
    JobOutput as JobStatusResponse,
    UserInfo as User,
    AppRoutersComputeModelsStatus as JobStatus,
)

SFAPI_TOKEN_URL = "https://oidc.nersc.gov/c2id/token"
SFAPI_BASE_URL = "https://api.nersc.gov/api/v1.2"


class AsyncClient:
    def __init__(
        self,
        client_id: Optional[str] = None,
        secret: Optional[str] = None,
        key_name: Optional[str] = None,
    ):
        if any(arg is None for arg in [client_id, secret]):
            self._get_client_secret_from_file(key_name)
        else:
            self._client_id = client_id
            self._secret = secret
        self._oauth2_session = None

    async def __aenter__(self):
        self._oauth2_session = AsyncOAuth2Client(
            client_id=self._client_id,
            client_secret=self._secret,
            token_endpoint_auth_method=PrivateKeyJWT(SFAPI_TOKEN_URL),
            grant_type="client_credentials",
            token_endpoint=SFAPI_TOKEN_URL,
            timeout=10.0,
        )

        await self._oauth2_session.fetch_token()

        return self

    async def __aexit__(self, type, value, traceback):
        if self._oauth2_session is not None:
            await self._oauth2_session.aclose()

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
                raise SfApiError(f"No keys found in {keys.as_posix()}")
            key_path = Path(key_paths[0])

        # Check that key is read only in case it's not
        # 0o100600 means chmod 600
        if key_path.stat().st_mode != 0o100600:
            raise SfApiError(
                f"Incorrect permissions on the key. To fix run: chmod 600 {key_path}"
            )

        with Path(key_path).open() as secret:
            if key_path.suffix == ".json":
                json_web_key = json.loads(secret.read())
                self._secret = JsonWebKey.import_key(json_web_key["secret"])
                self._client_id = json_web_key["client_id"]
            else:
                self._secret = secret.read()
                # Read in client_id from first line of file
                self._client_id = self._secret.split("\n")[0]

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(httpx.TimeoutException)
        | tenacity.retry_if_exception_type(httpx.ConnectError)
        | tenacity.retry_if_exception_type(httpx.HTTPStatusError),
        wait=tenacity.wait_exponential(max=10),
        stop=tenacity.stop_after_attempt(10),
    )
    async def get(self, url: str, params: Dict[str, Any] = {}) -> httpx.Response:
        await self._oauth2_session.ensure_active_token(self._oauth2_session.token)

        r = await self._oauth2_session.get(
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
    async def post(self, url: str, data: Dict[str, Any]) -> httpx.Response:
        await self._oauth2_session.ensure_active_token(self._oauth2_session.token)

        r = await self._oauth2_session.post(
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
    async def put(
        self, url: str, data: Dict[str, Any] = None, files: Dict[str, Any] = None
    ) -> httpx.Response:
        await self._oauth2_session.ensure_active_token(self._oauth2_session.token)

        r = await self._oauth2_session.put(
            f"{SFAPI_BASE_URL}/{url}",
            headers={
                "Authorization": self._oauth2_session.token["access_token"],
                "accept": "application/json",
            },
            data=data,
            files=files,
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
    async def delete(self, url: str) -> httpx.Response:
        await self._oauth2_session.ensure_active_token(self._oauth2_session.token)

        r = await self._oauth2_session.delete(
            f"{SFAPI_BASE_URL}/{url}",
            headers={
                "Authorization": self._oauth2_session.token["access_token"],
                "accept": "application/json",
            },
        )
        r.raise_for_status()

        return r

    async def compute(self, machine: Machines) -> Compute:
        response = await self.get(f"status/{machine.value}")

        compute = Compute.parse_obj(response.json())
        compute.client = self

        return compute

    async def user(self, username: Optional[str] = None) -> User:
        params = {}
        if username is not None:
            params["username"] = username

        response = await self.get("account/", params)
        json_response = response.json()

        return User.parse_obj(json_response)
