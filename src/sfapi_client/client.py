from __future__ import annotations
from typing import Dict, Any

from authlib.integrations.httpx_client.oauth2_client import AsyncOAuth2Client
from authlib.oauth2.rfc7523 import PrivateKeyJWT
import httpx

from .compute import Machines, Compute
from .common import SfApiError

SFAPI_TOKEN_URL = "https://oidc.nersc.gov/c2id/token"
SFAPI_BASE_URL = "https://api.nersc.gov/api/v1.2"


class Client:
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
        response = await self.get(f"status/{machine}")

        compute = Compute.parse_obj(response.json())
        compute.client = self

        return compute

    async def _fetch_job_status(self, jobid: int):
        params = {"sacct": True}
        r = await self.get(f"compute/jobs/cori/{jobid}", params)
        r.raise_for_status()

        json_response = r.json()
        if json_response.get("status").lower() != "ok":
            error = json_response["error"]
            raise SfApiError(error)

        output = json_response["output"]

        return output[0]
