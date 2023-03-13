from typing import Union, Optional, List
from pathlib import PurePosixPath
from pydantic import PrivateAttr
from io import StringIO, BytesIO
from base64 import b64decode

from .._models import (
    DirectoryEntry as PathBase,
    FileDownload as FileDownloadResponse,
    AppRoutersUtilsModelsStatus as FileDownloadResponseStatus,
    DirectoryOutput as DirectoryListingResponse,
    AppRoutersUtilsModelsStatus as DirectoryListingResponseStatus,
)
from .common import SfApiError


class RemotePath(PathBase):
    """
    RemotePath is used to model a remote path, it takes inspiration from
    pathlib and shares some of its interface.
    """

    compute: Optional["Compute"]
    # It would be nice to be able subclass PurePosixPath, however, this
    # require using private interfaces. So we derive by composition.
    _path: PurePosixPath = PrivateAttr()

    def __init__(self, path=None, **kwargs):
        super().__init__(**kwargs)
        self._path = PurePosixPath(path)

        if self.name is None:
            self.name = self._path.name

    def __truediv__(self, key):
        return RemotePath(str(self._path / key))

    def __rtruediv__(self, key):
        return RemotePath(str(key / self._path))

    def __str__(self):
        return str(self._path)

    @property
    def parent(self):
        return RemotePath(str(self._path.parent))

    @property
    def parents(self):
        return [RemotePath(str(p)) for p in self._path.parents]

    @property
    def stem(self):
        return self._path.stem

    @property
    def suffix(self):
        return self._path.suffix

    @property
    def suffixes(self):
        return self._path.suffixes

    @property
    def parts(self):
        return self._path.parts

    async def download(self, binary=False) -> Union[StringIO, BytesIO]:
        if self.perms[0] == "d":
            raise IsADirectoryError(self._path)

        r = await self.compute.client.get(
            f"utilities/download/{self.compute.name}/{self._path}?binary={binary}"
        )
        json_response = r.json()
        download_response = FileDownloadResponse.parse_obj(json_response)

        if download_response.status == FileDownloadResponseStatus.ERROR:
            raise SfApiError(download_response.error)

        file_data = download_response.file
        if download_response.is_binary:
            binary_file_data = b64decode(file_data)
            return BytesIO(binary_file_data)
        else:
            return StringIO(file_data)

    @staticmethod
    async def _ls(compute: "Compute", path) -> List["RemotePath"]:
        r = await compute.client.get(f"utilities/ls/{compute.name}/{path}")

        json_response = r.json()
        directory_listing_response = DirectoryListingResponse.parse_obj(json_response)
        if directory_listing_response.status == DirectoryListingResponseStatus.ERROR:
            raise SfApiError(directory_listing_response.error)

        paths = []

        def _to_remote_path(path, entry):
            kwargs = entry.dict()
            kwargs.update(path=path)
            p = RemotePath(**kwargs)
            p.compute = compute

            return p

        # Special case for listing file
        if len(directory_listing_response.entries) == 1:
            entry = directory_listing_response.entries[0]
            # The API can add an extra /
            path = entry.name
            if entry.name.startswith("//"):
                path = path[1:]
            filename = PurePosixPath(path).name
            entry.name = filename
            paths.append(_to_remote_path(path, entry))
        else:
            for entry in directory_listing_response.entries:
                paths.append(_to_remote_path(f"{path}/{entry.name}", entry))

        return paths

    async def ls(self) -> List["RemotePath"]:
        return await self._ls(self.compute, str(self._path))
