from typing import List, Optional, Callable
from functools import wraps

from pydantic import ConfigDict

from ..exceptions import SfApiError


from .._models import (
    BodyStartGlobusTransferStorageGlobusPost as GlobusBase,
    GlobusTransfer, GlobusTransferResult

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


class AsyncTransfer(GlobusBase):
    client: Optional["AsyncClient"]  # noqa: F821

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    @check_auth
    async def globus_tranfser(
        client,
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
        print(body)
        r = await client.post("storage/globus", data=body)
        json_response = r.json()
        return GlobusTransfer.model_validate(json_response)

    @staticmethod
    @check_auth
    async def check_globus_tranfser(
        client,
        transfer_uuid
    ):
        r = await client.get(f"storage/globus/{transfer_uuid}")
        json_response = r.json()
        return GlobusTransferResult.model_validate(json_response)
