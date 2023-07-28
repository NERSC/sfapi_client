from __future__ import annotations
from typing import Dict, Any, Optional, cast, List, Union
from pathlib import Path
import json

from authlib.integrations.httpx_client.oauth2_client import OAuth2Client
from authlib.oauth2.rfc7523 import PrivateKeyJWT
import httpx
import tenacity
from authlib.jose import JsonWebKey

from .compute import Machine, Compute
from ..exceptions import SfApiError
from .._models import (
    JobOutput as JobStatusResponse,
    AppRoutersComputeModelsStatus as JobStatus,
    Changelog as ChangelogItem,
    Config as ConfItem,
    Outage,
    Note,
    AppRoutersStatusModelsStatus as Status,
)
from .._models.resources import Resource
from .groups import Group, GroupMember
from .users import User
from .projects import Project, Role
from .paths import RemotePath

SFAPI_TOKEN_URL = "https://oidc.nersc.gov/c2id/token"
SFAPI_BASE_URL = "https://api.nersc.gov/api/v1.2"
MAX_RETRY = 10


# Retry on httpx.HTTPStatusError recoverable status codes
class retry_if_http_status_error(tenacity.retry_if_exception):
    def __init__(self):
        super().__init__(self._retry)

    def _retry(self, e: Exception):
        retry_codes = [
            httpx.codes.TOO_MANY_REQUESTS,
            httpx.codes.BAD_GATEWAY,
            httpx.codes.SERVICE_UNAVAILABLE,
            httpx.codes.GATEWAY_TIMEOUT,
        ]
        return (
            isinstance(e, httpx.HTTPStatusError)
            and cast(httpx.HTTPStatusError, e).response.status_code in retry_codes
        )


class Api:
    """
    API information.
    """

    def __init__(self, client: "Client"):
        self._client = client

    def changelog(self) -> List[ChangelogItem]:
        """
        Get the API changelog.

        :return: The API changelog
        :rtype: List[ChangelogItem]
        """
        r = self._client.get("meta/changelog")

        json_response = r.json()

        return [ChangelogItem.model_validate(i) for i in json_response]

    def config(self) -> Dict[str, str]:
        """
        Get the configuration information for the API.

        :return: The API configuration
        :rtype: Dict[str, str]
        """
        r = self._client.get("meta/config")

        json_response = r.json()

        config_items = [ConfItem.model_validate(i) for i in json_response]

        config = {}
        for i in config_items:
            config[i.key] = i.value

        return config


StatusInfo = Union[Outage, Note, Status]


class Resources:
    def __init__(self, client: "Client"):
        self._client = client

    @staticmethod
    def _resource_name(resource_name: Optional[Union[str, Machine]]):
        if resource_name is None:
            resource_name = ""
        else:
            resource_name = f"/{resource_name}"

        return resource_name

    @staticmethod
    def _list_to_resource_map(
        info_list: List[List[StatusInfo]],
    ) -> Dict[str, List[StatusInfo]]:
        resource_map = {}

        for resource_info_list in info_list:
            for info in resource_info_list:
                resource_info = resource_map.setdefault(info.name, [])
                resource_info.append(info)

        return resource_map

    def outages(
        self, resource_name: Optional[Union[str, Machine]] = None
    ) -> Union[Dict[str, List[Outage]], List[Outage]]:
        """
        Get outage information for a resource.

        :param resource_name: The resource name
        :return: The outages
        :rtype: Union[Dict[str, List[Outage]], List[Outage]]
        """
        resource_path = self._resource_name(resource_name)
        response = self._client.get(f"status/outages{resource_path}")
        json_response = response.json()

        if resource_name:
            outages = [Outage.model_validate(o) for o in json_response]
        else:
            outages = [[Outage.model_validate(o) for o in r] for r in json_response]
            outages = self._list_to_resource_map(outages)

        return outages

    def planned_outages(
        self, resource_name: Optional[Union[str, Machine]] = None
    ) -> Union[Dict[str, List[Outage]], List[Outage]]:
        """
        Get planned outage information for a resource.

        :param resource_name: The resource name
        :return: The planned outages
        :rtype: Union[Dict[str, List[Outage]], List[Outage]]
        """
        resource_path = self._resource_name(resource_name)
        response = self._client.get(f"status/outages/planned{resource_path}")
        json_response = response.json()

        if resource_name:
            outages = [Outage.model_validate(o) for o in json_response]
        else:
            outages = [[Outage.model_validate(o) for o in r] for r in json_response]
            outages = self._list_to_resource_map(outages)

        return outages

    def notes(
        self, resource_name: Optional[Union[str, Machine]] = None
    ) -> Union[Dict[str, List[Note]], List[Note]]:
        """
        Get notes associated with a resource.

        :param resource_name: The resource name
        :return: The resource notes
        :rtype: Union[Dict[str, List[Note]], List[Note]]
        """
        resource_path = self._resource_name(resource_name)
        response = self._client.get(f"status/notes{resource_path}")
        json_response = response.json()

        if resource_name:
            notes = [Note.model_validate(n) for n in json_response]
        else:
            notes = [[Note.model_validate(n) for n in r] for r in json_response]
            notes = self._list_to_resource_map(notes)

        return notes

    def status(
        self, resource_name: Optional[Union[str, Machine, Resource]] = None
    ) -> Union[Dict[str, Status], Status]:
        """
        Get the status of a resource.

        :param resource_name: The resource name
        :return: The resource status
        :rtype: Union[Dict[str, Status], Status]
        """
        resource_path = self._resource_name(resource_name)

        response = self._client.get(f"status{resource_path}")
        json_response = response.json()

        if resource_name:
            status = Status.model_validate(json_response)
        else:
            status = [Status.model_validate(s) for s in json_response]
            status = {s.name: s for s in status}

        return status


class Client:
    def __init__(
        self,
        client_id: Optional[str] = None,
        secret: Optional[str] = None,
        key: Optional[Union[str, Path]] = None,
        api_base_url: Optional[str] = SFAPI_BASE_URL,
        token_url: Optional[str] = SFAPI_TOKEN_URL,
        wait_interval: int = 10,
    ):
        """
        Create a client instance.

        Usage:

        ```python
        >>> from sfapi_client import Client
        >>> with Client(client_id, client_secret) as client:
        >>>    # Use client
        ```

        :param client_id: The client ID
        :param secret: The client secret

        :return: The client instance
        :rtype: Client
        """
        self._client_id = None
        self._secret = None
        if any(arg is None for arg in [client_id, secret]):
            self._read_client_secret_from_file(key)
        else:
            self._client_id = client_id
            self._secret = secret
        self._api_base_url = api_base_url
        self._token_url = token_url
        self._client_user = None
        self.__oauth2_session = None
        self._api = None
        self._resources = None
        self._wait_interval = wait_interval

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
                token_endpoint_auth_method=PrivateKeyJWT(self._token_url),
                grant_type="client_credentials",
                token_endpoint=self._token_url,
                timeout=10.0,
            )

            self.__oauth2_session.fetch_token()
        else:
            # We have a session
            # Make sure it's still active
            self.__oauth2_session.ensure_active_token(self.__oauth2_session.token)

        return self.__oauth2_session

    @property
    def token(self) -> str:
        """
        Bearer token string which can be helpful for debugging through swagger UI.
        """

        if self._client_id is not None:
            oauth_session = self._oauth2_session()
            return oauth_session.token["access_token"]

    def close(self):
        """
        Release resources associated with the client instance.
        """
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
        if key_path is None or key_path.is_dir():
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
        wait=tenacity.wait_exponential(max=MAX_RETRY),
        stop=tenacity.stop_after_attempt(MAX_RETRY),
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
        wait=tenacity.wait_exponential(max=MAX_RETRY),
        stop=tenacity.stop_after_attempt(MAX_RETRY),
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
        wait=tenacity.wait_exponential(max=MAX_RETRY),
        stop=tenacity.stop_after_attempt(MAX_RETRY),
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
        wait=tenacity.wait_exponential(max=MAX_RETRY),
        stop=tenacity.stop_after_attempt(MAX_RETRY),
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

    def compute(self, machine: Union[Machine, str]) -> Compute:
        """Create a compute site to submit jobs or view jobs in the queue

        :param machine: Name of the compute machine to use
        :return: Compute object that can be used to start jobs,
        view the queue on the system, or list files and directories.
        """
        # Allows for creating a compute from a name string
        machine = Machine(machine)
        response = self.get(f"status/{machine.value}")

        values = response.json()
        values["client"] = self
        compute = Compute.model_validate(values)

        return compute

    # Get the user associated with the credentials
    def _user(self):
        if self._client_user is None:
            self._client_user = self.user()

        return self._client_user

    def user(self, username: Optional[str] = None) -> User:
        """
        Get a user.

        :param username: The username
        :return: The user
        :rtype: UserGroup
        """
        return User._fetch_user(self, username)

    def group(self, name: str) -> Group:
        """
        Get a group.

        :param name: The group name
        :return: The group
        :rtype: Group
        """
        return Group._fetch_group(self, name)

    @property
    def api(self) -> Api:
        """
        API related information.
        """
        if self._api is None:
            self._api = Api(self)

        return self._api

    @property
    def resources(self) -> Resources:
        """
        Resource related information.
        """
        if self._resources is None:
            self._resources = Resources(self)

        return self._resources


Compute.model_rebuild()
Group.model_rebuild()
User.model_rebuild()
Project.model_rebuild()
RemotePath.model_rebuild()
Role.model_rebuild()
GroupMember.model_rebuild()
