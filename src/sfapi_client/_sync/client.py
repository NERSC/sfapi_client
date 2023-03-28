from __future__ import annotations
from typing import Dict, Any, Optional, cast, List
from pathlib import Path
import json

from authlib.integrations.httpx_client.oauth2_client import OAuth2Client
from authlib.oauth2.rfc7523 import PrivateKeyJWT
import httpx
import tenacity
from authlib.jose import JsonWebKey

from .compute import Machines, Compute
from ..common import SfApiError
from .._models import (
    JobOutput as JobStatusResponse,
    AppRoutersComputeModelsStatus as JobStatus,
    Changelog as ChangelogItem,
    Config as ConfItem,
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


class Api:
    def __init__(self, client: "Client"):
        self._client = client

    def changelog(self) -> List[ChangelogItem]:
        r = self._client.get("meta/changelog")

        json_response = r.json()

        return [ChangelogItem.parse_obj(i) for i in json_response]

    def config(self) -> Dict[str, str]:
        r = self._client.get("meta/config")

        json_response = r.json()

        config_items = [ConfItem.parse_obj(i) for i in json_response]

        config = {}
        for i in config_items:
            config[i.key] = i.value

        return config


class Client:
    """
    Create a client instance

    :param client_id: The client ID
    :type client_id: str
    :param secret: The client secret
    :type secret: str
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        secret: Optional[str] = None,
        key_name: Optional[str] = None,
        api_base_url: Optional[str] = SFAPI_BASE_URL,
    ):
        self._client_id = None
        if any(arg is None for arg in [client_id, secret]):
            self._read_client_secret_from_file(key_name)
        else:
            self._client_id = client_id
            self._secret = secret
        self._api_base_url = api_base_url
        self._client_user = None
        self.__oauth2_session = None
        self._api = None

    def __enter__(self):
        return self

    def _oauth2_session(self):
        if self._client_id is None:
            raise SfApiError(f"No credentials have been provides")

        if self.__oauth2_session is None:
            # Create a new session if we haven't already
            self.__oauth2_session = OAuth2Client(
                client_id=self._client_id,
                client_secret=self._secret,
                token_endpoint_auth_method=PrivateKeyJWT(SFAPI_TOKEN_URL),
                grant_type="client_credentials",
                token_endpoint=SFAPI_TOKEN_URL,
                timeout=10.0,
            )

            self.__oauth2_session.fetch_token()
        else:
            # We have a session
            # Make sure it's still active
            self.__oauth2_session.ensure_active_token(self.__oauth2_session.token)

        return self.__oauth2_session

    def close(self):
        if self.__oauth2_session is not None:
            self.__oauth2_session.close()

    def __exit__(self, type, value, traceback):
        self.close()

    def _read_client_secret_from_file(self, name):
        if name is not None and Path(name).exists():
            # If the user gives a full path, then use it
            key_path = Path(name)
        else:
            # If not let's search in ~/.superfacility for the name or any key
            nickname = "" if name is None else name
            keys = Path().home() / ".superfacility"
            key_paths = list(keys.glob(f"{nickname}*"))
            key_path = None
            if len(key_paths) == 1:
                key_path = Path(key_paths[0])

        # We have no credentials
        if key_path is None:
            return

        # Check that key is read only in case it's not
        # 0o100600 means chmod 600
        if key_path.stat().st_mode != 0o100600:
            raise SfApiError(
                f"Incorrect permissions on the key. To fix run: chmod 600 {key_path}"
            )

        with Path(key_path).open() as secret:
            if key_path.suffix == ".json":
                # Json file in the format {"client_id": "", "secret": ""}
                json_web_key = json.loads(secret.read())
                self._secret = JsonWebKey.import_key(json_web_key["secret"])
                self._client_id = json_web_key["client_id"]
            else:
                self._secret = secret.read()
                # Read in client_id from first line of file
                self._client_id = self._secret.split("\n")[0]

        # Get just client_id in case of spaces
        self._client_id = self._client_id.strip(" ")

        # Validate we got a correct looking client_id
        if len(self._client_id) != 13:
            raise SfApiError(f"client_id not found in file {key_path}")

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(httpx.TimeoutException)
        | tenacity.retry_if_exception_type(httpx.ConnectError)
        | retry_if_http_status_error(),
        wait=tenacity.wait_exponential(max=10),
        stop=tenacity.stop_after_attempt(10),
    )
    def get(self, url: str, params: Dict[str, Any] = {}) -> httpx.Response:
        if self._client_id is not None:
            oauth_session = self._oauth2_session()

            r = oauth_session.get(
                f"{self._api_base_url}/{url}",
                headers={
                    "Authorization": oauth_session.token["access_token"],
                    "accept": "application/json",
                },
                params=params,
            )
        # Use regular client if we are hitting an endpoint that don't need
        # auth.
        else:
            with httpx.Client() as client:
                r = client.get(
                    f"{self._api_base_url}/{url}",
                    headers={
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
        oauth_session = self._oauth2_session()

        r = oauth_session.post(
            f"{self._api_base_url}/{url}",
            headers={
                "Authorization": oauth_session.token["access_token"],
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
        oauth_session = self._oauth2_session()

        r = oauth_session.put(
            f"{self._api_base_url}/{url}",
            headers={
                "Authorization": oauth_session.token["access_token"],
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
        oauth_session = self._oauth2_session()

        r = oauth_session.delete(
            f"{self._api_base_url}/{url}",
            headers={
                "Authorization": oauth_session.token["access_token"],
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
        return User._fetch_user(self, username)

    def group(self, name: str) -> Group:
        return Group._fetch_group(self, name)

    @property
    def api(self):
        if self._api is None:
            self._api = Api(self)

        return self._api
