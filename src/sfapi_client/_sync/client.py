from __future__ import annotations
from typing import Dict, Any, Optional, cast
from pydantic import PrivateAttr


from authlib.integrations.httpx_client.oauth2_client import OAuth2Client
from authlib.oauth2.rfc7523 import PrivateKeyJWT
import httpx
import tenacity

from .compute import Machines, Compute
from ..common import SfApiError
from .._models import (
    JobOutput as JobStatusResponse,
    AppRoutersComputeModelsStatus as JobStatus,
)
from .group import Group
from .user import User

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


class Client:
    """
    Create a client instance

    :param client_id: The client ID
    :type client_id: str
    :param secret: The client secret
    :type secret: str
    """

    def __init__(self, client_id, secret):
        self._client_id = client_id
        self._secret = secret
        self._oauth2_session = None
        self._client_user = None

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

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(httpx.TimeoutException)
        | tenacity.retry_if_exception_type(httpx.ConnectError)
        | retry_if_http_status_error(),
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
        | retry_if_http_status_error(),
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
        | retry_if_http_status_error(),
        wait=tenacity.wait_exponential(max=10),
        stop=tenacity.stop_after_attempt(10),
    )
    def put(
        self, url: str, data: Dict[str, Any] = None, files: Dict[str, Any] = None
    ) -> httpx.Response:
        self._oauth2_session.ensure_active_token(self._oauth2_session.token)

        r = self._oauth2_session.put(
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

    # Get the user associated with the credentials
    def _user(self):
        if self._client_user is None:
            self._client_user = self.user()

        return self._client_user

    def user(self, username: Optional[str] = None) -> User:
        url = "account/"
        if username is not None:
            url = f"{url}?{username}"

        response = self.get(url)
        json_response = response.json()

        user = User.parse_obj(json_response)
        user.client = self

        return user

    def group(self, name: str) -> Group:
        response = self.get(f"account/groups/{name}")
        json_response = response.json()

        group = Group.parse_obj(json_response)
        group.client = self

        return group
