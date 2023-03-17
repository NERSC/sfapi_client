from __future__ import annotations
from typing import Dict, Any, Optional, cast

from authlib.integrations.httpx_client.oauth2_client import AsyncOAuth2Client
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


# Retry on httpx.HTTPStatusError if status code is not 401 or 403
class retry_if_http_status_error(tenacity.retry_if_exception):
    def __init__(self):
        super().__init__(self._retry)

    def _retry(self, e: Exception):
        dont_retry_codes = [httpx.codes.FORBIDDEN, httpx.codes.UNAUTHORIZED]
        return (
            isinstance(e, httpx.HTTPStatusError)
            and cast(httpx.HTTPStatusError, e).response.status_code
            not in dont_retry_codes
        )


class AsyncClient:
    def __init__(self, client_id, secret):
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

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(httpx.TimeoutException)
        | tenacity.retry_if_exception_type(httpx.ConnectError)
        | retry_if_http_status_error(),
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
        | retry_if_http_status_error(),
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
        | retry_if_http_status_error(),
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
        | retry_if_http_status_error(),
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
