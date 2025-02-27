from pathlib import Path
from typing import Callable, Optional, Union
from functools import wraps

from ..paths import AsyncRemotePath

from ..exceptions import SfApiError

from .._models import (
    GlobusTransfer,
    GlobusTransferResult,
)


def check_auth(method: Callable):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self._client is None:
            raise SfApiError(
                f"Cannot call {self.__class__.__name__}.{method.__name__}() with an unauthenticated client."  # noqa: E501
            )
        return method(self, *args, **kwargs)

    return wrapper


class AsyncGlobus:
    def __init__(self, client):
        self._client = client

    @check_auth
    async def start_transfer(
        self,
        source_uuid: str,
        target_uuid: str,
        source_dir: Union[str, Path, AsyncRemotePath],
        target_dir: Union[str, Path, AsyncRemotePath],
        label: Optional[str] = None,
    ) -> GlobusTransfer:
        """Start a Globus transfer throught the SuperFacility API

        - Must select the Globus option when creating the SuperFacility key

        ```python
        >>> from sfapi_client import AsyncClient
        >>> async with AsyncClient(client_id, client_secret) as client:
        >>>     res = await client.storage.globus.start_tranfser(
                        "dtn",
                        "dtn",
                        "/pscratch/sd/u/user/globus",
                        "/global/cfs/cdirs/m0000/globus"
                    )
        ```


        :param str source_uuid: Globus UUID for the source collection
        :param str target_uuid: Globus UUID for the target collection
        :param str source_dir: Path to file or directory on the source to transfer
        :param str target_dir: Path to directory on the target to transfer files to
        :param Optional[str] label: Label for the transfer, defaults to None
        :return GlobusTransfer
        """

        if None in [source_uuid, target_uuid, source_dir, target_dir]:
            # Check that all parametes are not none
            raise ValueError("source_uuid, target_uuid, source_dir, and target_dir cannot be None")

        body = {
            "source_uuid": source_uuid,
            "target_uuid": target_uuid,
            "source_dir": source_dir,
            "target_dir": target_dir,
            "label": label,
        }

        r = await self._client.post("storage/globus/transfer", data=body)
        json_response = r.json()
        return GlobusTransfer.model_validate(json_response)

    @check_auth
    async def check_transfer(self, transfer_uuid: str) -> GlobusTransferResult:
        """Check on Globus transfer status

        - Must select the Globus option when creating the SuperFacility key

        >>> from sfapi_client import AsyncClient
        >>> async with AsyncClient(client_id, client_secret) as client:
        >>>     res = await client.storage.globus.check_transfer(
                        "globus-transfer-uuid"
                    )

        :param str transfer_uuid: Globus UUID for the transfer
        :return GlobusTransferResult
        """
        if transfer_uuid is None:
            raise ValueError("Must provide a transfer_uuid")

        r = await self._client.get(f"storage/globus/transfer/{transfer_uuid}")
        json_response = r.json()
        return GlobusTransferResult.model_validate(json_response)


class AsyncStorage:
    def __init__(self, client):
        self._client = client
        self._globus = None

    @property
    def globus(self) -> AsyncGlobus:
        """
        Storage related methods

         - start_tranfser
         - check_transfer
        """

        if self._globus is None:
            self._globus = AsyncGlobus(self._client)

        return self._globus
