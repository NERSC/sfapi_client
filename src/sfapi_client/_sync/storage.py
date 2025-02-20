from typing import Callable, Optional
from functools import wraps

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


class Storage:
    def __init__(self, client):
        self._client = client

    @check_auth
    def start_globus_transfer(
        self,
        source_uuid: str,
        target_uuid: str,
        source_dir: str,
        target_dir: str,
        label: Optional[str] = None,
    ) -> GlobusTransfer:
        """Start a Globus transfer throught the SuperFacility API

        - Must select the Globus option when creating the SuperFacility key

        ```python
        >>> from sfapi_client import Client
        >>> with Client(client_id, client_secret) as client:
        >>>     res = client.storage.start_globus_tranfser(
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
        body = {
            "source_uuid": source_uuid,
            "target_uuid": target_uuid,
            "source_dir": source_dir,
            "target_dir": target_dir,
            "label": label,
        }

        r = self._client.post("storage/globus/transfer", data=body)
        json_response = r.json()
        return GlobusTransfer.model_validate(json_response)

    @check_auth
    def check_globus_transfer(self, transfer_uuid: str) -> GlobusTransferResult:
        """Check on Globus transfer status

        - Must select the Globus option when creating the SuperFacility key

        >>> from sfapi_client import Client
        >>> with Client(client_id, client_secret) as client:
        >>>     res = client.storage.check_globus_transfer(
                        "globus-transfer-uuid"
                    )

        :param str transfer_uuid: Globus UUID for the transfer
        :return GlobusTransferResult
        """
        r = self._client.get(f"storage/globus/transfer/{transfer_uuid}")
        json_response = r.json()
        return GlobusTransferResult.model_validate(json_response)
