from pathlib import Path
from typing import Callable, Optional, Union, List, Any
from functools import wraps
from pydantic import ConfigDict
from abc import ABC
import sys
import math

from .._utils import _SLEEP
from ..paths import RemotePath

from ..exceptions import SfApiError

from .compute import Machine
from .._models import (
    AppRoutersStatusModelsStatus as StorageBase,
    GlobusTransfer as GlobusTransferModel,
    BodyStartGlobusTransferStorageGlobusTransferPost as GlobusBodyPost,
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


class Storage:
    def __init__(self, client: "Client"):  # noqa: F821
        self.client = client

    def globus(
        self,
    ):
        """Create a globus transfer object to start and monitor transfers

        - Must select the Globus option when creating the SuperFacility key

        ```python
        >>> from sfapi_client import Client
        >>> with Client(client_id, client_secret) as client:
        >>>     globus = client.storage.globus(Machine.dtns, Machine.dtns)
        ```

        :param Union[Machine, str, None] source_machine: Source collecton name or Globus UUID, defaults to None
        :param Union[Machine, str, None] target_machine: Destincation collection name or Globus UUID, defaults to None
        :return GlobusStorage: Globus object to start and monitor transfers
        """
        response = self.client.get("status/globus")
        values = response.json()
        values["client"] = self.client
        _globus = Globus.model_validate(values)

        return _globus


class SyncGlobusTransfer(GlobusTransferResult, ABC):
    globus: Optional["Globus"]  # noqa: F821
    transfer_id: str
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def update(self):
        """Updates the status of the transfer"""
        job_state = self._fetch_state()
        self._update(job_state)

    def _update(self, new_job_state: Any):
        for k in new_job_state.model_fields_set:
            v = getattr(new_job_state, k)
            setattr(self, k, v)

        return self

    def _wait_until(self, states: List[GlobusStatus], timeout: int = sys.maxsize):
        max_iteration = math.ceil(timeout / self.globus.client._wait_interval)
        iteration = 0

        while self.globus_status not in states:
            self.update()
            _SLEEP(self.globus.client._wait_interval)

            if iteration == max_iteration:
                raise TimeoutError()

            iteration += 1

        return self.globus_status

    def _wait_until_complete(self, timeout: int = sys.maxsize):
        return self._wait_until(GLOBUS_TERMINAL_STATES, timeout)

    def __await__(self):
        return self._wait_until_complete().__await__()

    def complete(self, timeout: int = sys.maxsize):
        """Wait for the transfer to complete

        >>> from sfapi_client import Client
        >>> with Client(client_id, client_secret) as client:
        >>>     globus = client.storage.globus()
        >>>     res = globus.transfer(
                        "globus-transfer-uuid"
                )
        >>>     res.complete()

        :param int timeout: time to wait for the transfer to complete, defaults to sys.maxsize
        :return GlobusStart: Gives the file status for the transfer
        """
        return self._wait_until_complete(timeout)

    def _fetch_state(self):
        r = self.globus.client.get(f"storage/globus/transfer/{self.transfer_id}")
        json_response = r.json()
        json_response["transfer_id"] = self.transfer_id
        json_response["globus"] = self.globus
        transfer = SyncGlobusTransfer.model_validate(json_response)
        return transfer


class Globus(StorageBase):
    client: Optional["Client"]  # noqa: F821
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @check_auth
    def start_transfer(
        self,
        source_machine: Union[Machine, str],
        target_machine: Union[Machine, str],
        source_dir: Union[str, Path, RemotePath],
        target_dir: Union[str, Path, RemotePath],
        label: Optional[str] = None,
    ) -> SyncGlobusTransfer:
        """Start a Globus transfer throught the SuperFacility API

        - Must select the Globus option when creating the SuperFacility key

        ```python
        >>> from sfapi_client import Client
        >>> with Client(client_id, client_secret) as client:
        >>>     globus = client.storage.globus(Machine.dtns, Machine.dtns)
        >>>     res = globus.start_transfer(
                        Machine.Perlmutter,
                        "/pscratch/sd/u/user/globus",
                        Machine.dtns,
                        "/global/cfs/cdirs/m0000/globus"
                    )
        ```

        :param str source_dir: Path to file or directory on the source to transfer
        :param str target_dir: Path to directory on the target to transfer files to
        :param Optional[str] label: Label for the transfer,
        defaults to None and the API will create a label for the transfer
        :return GlobusTransfer
        """

        if None in [source_machine, source_dir, target_machine, target_dir]:
            # Check that all parametes are not none
            raise ValueError("sources, and targets cannot be None")

        # Make machine names match those in the API endpoint
        source_name = (
            "dtn" if source_machine in [Machine.dtns, Machine.dtn01] else source_machine
        )
        target_name = (
            "dtn" if target_machine in [Machine.dtns, Machine.dtn01] else target_machine
        )

        body = GlobusBodyPost(
            source_uuid=source_name,
            target_uuid=target_name,
            source_dir=str(source_dir),
            target_dir=str(target_dir),
            label=label,
        )

        r = self.client.post("storage/globus/transfer", data=body.model_dump())
        new_transfer = GlobusTransferModel.model_validate(r.json())
        transfer_id = new_transfer.transfer_id
        r = self.client.get(f"storage/globus/transfer/{transfer_id}")
        json_response = r.json()
        json_response["transfer_id"] = transfer_id
        json_response["globus"] = self
        transfer = SyncGlobusTransfer.model_validate(json_response)
        return transfer

    @check_auth
    def transfer(self, transfer_id: str) -> GlobusTransferResult:
        """Check on Globus transfer status

        - Must select the Globus option when creating the SuperFacility key

        >>> from sfapi_client import Client
        >>> with Client(client_id, client_secret) as client:
        >>>     globus = client.storage.globus()
        >>>     res = globus.transfer(
                        "globus-transfer-uuid"
                )

        :param str transfer_uuid: Globus UUID for the transfer
        :return GlobusTransferResult
        """
        if transfer_id is None:
            raise ValueError("Must provide a transfer_uuid")

        r = self.client.get(f"storage/globus/transfer/{transfer_id}")
        json_response = r.json()
        json_response["transfer_id"] = transfer_id
        json_response["globus"] = self
        transfer = SyncGlobusTransfer.model_validate(json_response)
        return transfer
