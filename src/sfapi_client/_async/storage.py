from pathlib import Path
from typing import Callable, Optional, Union, List, Any
from functools import wraps
from pydantic import ConfigDict
from abc import ABC
import sys
import math

from .._utils import _ASYNC_SLEEP
from ..paths import AsyncRemotePath

from ..exceptions import SfApiError

from .compute import Machine
from .._models import (
    AppRoutersStatusModelsStatus as StorageBase,
    GlobusTransfer as GlobusTransferModel,
    GlobusTransferResult,
    GlobusStatus,
)

GLOBUS_TERMINAL_STATES = [
    GlobusStatus.CANCELED,
    GlobusStatus.FAILED,
    GlobusStatus.SUCCEEDED,
]


def check_auth(method: Callable):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.client is None:
            raise SfApiError(
                f"Cannot call {self.__class__.__name__}.{method.__name__}() with an unauthenticated client."  # noqa: E501
            )
        return method(self, *args, **kwargs)

    return wrapper


class AsyncStorage:
    def __init__(self, client: "AsyncClient"):  # noqa: F821
        self.client = client

    async def globus(
        self,
        source_machine: Union[Machine, str, None] = None,
        target_machine: Union[Machine, str, None] = None,
    ):
        """Create a globus transfer object to start and monitor transfers

        - Must select the Globus option when creating the SuperFacility key

        ```python
        >>> from sfapi_client import AsyncClient
        >>> async with AsyncClient(client_id, client_secret) as client:
        >>>     globus = client.storage.globus(Machine.dtns, Machine.dtns)
        ```

        :param Union[Machine, str, None] source_machine: Source collecton name or Globus UUID, defaults to None
        :param Union[Machine, str, None] target_machine: Destincation collection name or Globus UUID, defaults to None
        :return AsyncGlobusStorage: Globus object to start and monitor transfers
        """
        response = await self.client.get("status/globus")
        values = response.json()
        values["client"] = self.client
        values["source_machine"] = source_machine
        values["target_machine"] = target_machine
        _globus = AsyncGlobusStorage.model_validate(values)

        return _globus


class AsyncGlobusTransfer(GlobusTransferResult, ABC):
    globus: Optional["AsyncGlobusStorage"]  # noqa: F821
    transfer_id: str
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def update(self):
        """Updates the status of the transfer"""
        job_state = await self._fetch_state()
        self._update(job_state)

    def _update(self, new_job_state: Any):
        for k in new_job_state.model_fields_set:
            v = getattr(new_job_state, k)
            setattr(self, k, v)

        return self

    async def _wait_until(self, states: List[GlobusStatus], timeout: int = sys.maxsize):
        max_iteration = math.ceil(timeout / self.globus.client._wait_interval)
        iteration = 0

        while self.globus_status not in states:
            await self.update()
            await _ASYNC_SLEEP(self.globus.client._wait_interval)

            if iteration == max_iteration:
                raise TimeoutError()

            iteration += 1

        return self.globus_status

    async def _wait_until_complete(self, timeout: int = sys.maxsize):
        return await self._wait_until(GLOBUS_TERMINAL_STATES, timeout)

    def __await__(self):
        return self._wait_until_complete().__await__()

    async def complete(self, timeout: int = sys.maxsize):
        """Wait for the transfer to complete

        >>> from sfapi_client import AsyncClient
        >>> async with AsyncClient(client_id, client_secret) as client:
        >>>     globus = client.storage.globus()
        >>>     res = await globus.transfer(
                        "globus-transfer-uuid"
                )
        >>>     await res.complete()

        :param int timeout: time to wait for the transfer to complete, defaults to sys.maxsize
        :return GlobusStart: Gives the file status for the transfer
        """
        return await self._wait_until_complete(timeout)

    async def _fetch_state(self):
        r = await self.globus.client.get(f"storage/globus/transfer/{self.transfer_id}")
        json_response = r.json()
        json_response["transfer_id"] = self.transfer_id
        json_response["globus"] = self.globus
        transfer = AsyncGlobusTransfer.model_validate(json_response)
        return transfer


class AsyncGlobusStorage(StorageBase):
    client: Optional["AsyncClient"]  # noqa: F821
    source_machine: Optional[Union[Machine, str, None]]
    target_machine: Optional[Union[Machine, str, None]]
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @check_auth
    async def start_transfer(
        self,
        source_dir: Union[str, Path, AsyncRemotePath],
        target_dir: Union[str, Path, AsyncRemotePath],
        label: Optional[str] = None,
    ) -> AsyncGlobusTransfer:
        """Start a Globus transfer throught the SuperFacility API

        - Must select the Globus option when creating the SuperFacility key

        ```python
        >>> from sfapi_client import AsyncClient
        >>> async with AsyncClient(client_id, client_secret) as client:
        >>>     globus = client.storage.globus(Machine.dtns, Machine.dtns)
        >>>     res = await globus.start_transfer(
                        "/pscratch/sd/u/user/globus",
                        "/global/cfs/cdirs/m0000/globus"
                    )
        ```

        :param str source_dir: Path to file or directory on the source to transfer
        :param str target_dir: Path to directory on the target to transfer files to
        :param Optional[str] label: Label for the transfer,
        defaults to None and the API will create a label for the transfer
        :return AsyncGlobusTransfer
        """

        if None in [source_dir, target_dir]:
            # Check that all parametes are not none
            raise ValueError("source_dir, and target_dir cannot be None")

        # Make machine names match those in the API endpoint
        source_name = (
            "dtn"
            if self.source_machine in [Machine.dtns, Machine.dtn01]
            else self.source_machine
        )
        target_name = (
            "dtn"
            if self.target_machine in [Machine.dtns, Machine.dtn01]
            else self.target_machine
        )

        body = {
            "source_uuid": source_name,
            "target_uuid": target_name,
            "source_dir": source_dir,
            "target_dir": target_dir,
            "label": label,
        }

        r = await self.client.post("storage/globus/transfer", data=body)
        new_transfer = GlobusTransferModel.model_validate(r.json())
        transfer_id = new_transfer.transfer_id
        r = await self.client.get(f"storage/globus/transfer/{transfer_id}")
        json_response = r.json()
        json_response["transfer_id"] = transfer_id
        json_response["globus"] = self
        transfer = AsyncGlobusTransfer.model_validate(json_response)
        return transfer

    @check_auth
    async def transfer(self, transfer_id: str) -> GlobusTransferResult:
        """Check on Globus transfer status

        - Must select the Globus option when creating the SuperFacility key

        >>> from sfapi_client import AsyncClient
        >>> async with AsyncClient(client_id, client_secret) as client:
        >>>     globus = client.storage.globus()
        >>>     res = await globus.transfer(
                        "globus-transfer-uuid"
                )

        :param str transfer_uuid: Globus UUID for the transfer
        :return GlobusTransferResult
        """
        if transfer_id is None:
            raise ValueError("Must provide a transfer_uuid")

        r = await self.client.get(f"storage/globus/transfer/{transfer_id}")
        json_response = r.json()
        json_response["transfer_id"] = transfer_id
        json_response["globus"] = self
        transfer = AsyncGlobusTransfer.model_validate(json_response)
        return transfer
