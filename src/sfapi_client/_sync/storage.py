from typing import Callable
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
    def start_globus_tranfser(
        self,
        source_uuid: str,
        target_uuid: str,
        source_dir: str,
        target_dir: str,
        label: str | None = None,
    ) -> GlobusTransfer:
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
        r = self._client.get(f"storage/globus/transfer/{transfer_uuid}")
        json_response = r.json()
        return GlobusTransferResult.model_validate(json_response)
