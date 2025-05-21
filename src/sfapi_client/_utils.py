import time
import asyncio
from typing import Callable
from functools import wraps
from .exceptions import SfApiError
from ._models import StatusValue


_SLEEP = time.sleep
_ASYNC_SLEEP = asyncio.sleep


# def check_auth(method: Callable):
#     @wraps(method)
#     def wrapper(self, *args, **kwargs):
#         if self.client is None:
#             raise SfApiError(
#                 f"Cannot call {self.__class__.__name__}.{method.__name__}() with an unauthenticated client."  # noqa: E501
#             )
#         return method(self, *args, **kwargs)

#     return wrapper


def check_auth(method: Callable):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.client._client_id is None and self.client._access_token is None:
            raise SfApiError(
                f"Cannot call {self.__class__.__name__}.{method.__name__}() with an unauthenticated client."  # noqa: E501
            )
        elif self.status in [StatusValue.unavailable]:
            raise SfApiError(
                f"Resource {self.name} is {self.status.name}, {self.notes}"
            )
        return method(self, *args, **kwargs)

    return wrapper
