import time
import asyncio


class SfApiError(Exception):
    def __init__(self, message):
        self.message = message


_SLEEP = time.sleep
_ASYNC_SLEEP = asyncio.sleep
