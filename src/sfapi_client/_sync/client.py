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
from ..exceptions import ClientKeyError
from .._models import (
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
        access_token: Optional[str] = None,
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
        :param key: Full path to the client secret file, or path relative to `~` from the expanduser
        :param api_base_url: The API base URL
        :param token_url: The token URL
        :param access_token: An existing access token

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
        self.__http_client = None
        self._api = None
        self._resources = None
        self._wait_interval = wait_interval
        self._access_token = access_token

    def __enter__(self):
        return self

    def _http_client(self):
        headers = {"accept": "application/json"}
        # If we have a client_id then we need to use the OAuth2 client
        if self._client_id is not None:
            if self.__http_client is None:
                # Create a new session if we haven't already
                self.__http_client = OAuth2Client(
                    client_id=self._client_id,
                    client_secret=self._secret,
                    token_endpoint_auth_method=PrivateKeyJWT(self._token_url),
                    grant_type="client_credentials",
                    token_endpoint=self._token_url,
                    timeout=10.0,
                    headers=headers,
                )

                self.__http_client.fetch_token()
            else:
                # We have a session
                # Make sure it's still active
                self.__http_client.ensure_active_token(self.__http_client.token)
        # Use regular client, but add the access token if we have one
        elif self.__http_client is None:
            # We already have an access token
            if self._access_token is not None:
                headers.update({"Authorization": f"Bearer {self._access_token}"})

            self.__http_client = httpx.Client(headers=headers)

        return self.__http_client

    @property
    def token(self) -> str:
        """
        Bearer token string which can be helpful for debugging through swagger UI.
        """

        if self._access_token is not None:
            return self._access_token
        elif self._client_id is not None:
            client = self._http_client()
            return client.token["access_token"]

    def close(self):
        """
        Release resources associated with the client instance.
        """
        if self.__http_client is not None:
            self.__http_client.close()

    def __exit__(self, type, value, traceback):
        self.close()

    def _read_client_secret_from_file(self, name: Optional[Union[str, Path]]):
        if name is None:
            return
        _path = Path(name).expanduser().resolve()
        if _path.exists():
            # If the user gives a full path, then use it
            key_path = _path
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
            raise ClientKeyError(
                f"no key found at key_path: {_path} or in ~/.superfacility/{name}*"
            )

        # Check that key is read only in case it's not
        # 0o100600 means chmod 600
        if key_path.stat().st_mode != 0o100600:
            raise ClientKeyError(
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
            raise ClientKeyError(f"client_id not found in file {key_path}")

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(httpx.TimeoutException)
        | tenacity.retry_if_exception_type(httpx.ConnectError)
        | retry_if_http_status_error(),
        wait=tenacity.wait_exponential(max=MAX_RETRY),
        stop=tenacity.stop_after_attempt(MAX_RETRY),
    )
    def get(self, url: str, params: Dict[str, Any] = {}) -> httpx.Response:
        client = self._http_client()
        r = client.get(
            f"{self._api_base_url}/{url}",
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
        client = self._http_client()

        r = client.post(
            f"{self._api_base_url}/{url}",
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
        client = self._http_client()

        r = client.put(
            f"{self._api_base_url}/{url}",
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
        client = self._http_client()

        r = client.delete(
            f"{self._api_base_url}/{url}",
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

# Ensure that the job models are built, we need to import here to
# avoid circular imports
from .jobs import JobSacct, JobSqueue  # noqa: E402

JobSqueue.model_rebuild()
JobSacct.model_rebuild()
