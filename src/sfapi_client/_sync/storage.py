from typing import Optional, Callable
from functools import wraps

from pydantic import ConfigDict

from ..exceptions import SfApiError


from .._models import (
    BodyStartGlobusTransferStorageGlobusPost as GlobusBase,
    GlobusTransfer,
    GlobusTransferResult
)


def check_auth(method: Callable):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self._client_id is None:
            raise SfApiError(
                f"Cannot call {self.__class__.__name__}.{method.__name__}() with an unauthenticated client."  # noqa: E501
            )
        return method(self, *args, **kwargs)

    return wrapper


class Transfer(GlobusBase):
    def __init__(self, client: "Client"):
        self._client = client

    @staticmethod
    @check_auth
    def start_globus_tranfser(
        self,
        source_uuid: str,
        target_uuid: str,
        source_dir: str,
        target_dir: str,
    ):
        body: GlobusBase = {
            "source_uuid": source_uuid,
            "target_uuid": target_uuid,
            "source_dir": source_dir,
            "target_dir": target_dir
        }
        r = self._client.post("storage/globus", data=body)
        json_response = r.json()
        return GlobusTransfer.model_validate(json_response)

    @staticmethod
    @check_auth
    def check_globus_tranfser(
        self,
        transfer_uuid: str
    ):
        r = self._client.get(f"storage/globus/{transfer_uuid}")
        json_response = r.json()
        return GlobusTransferResult.model_validate(json_response)
