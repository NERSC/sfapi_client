from typing import Optional, List, IO, AnyStr, Dict
from pathlib import PurePosixPath
from pydantic import PrivateAttr
from io import StringIO, BytesIO
from base64 import b64decode
import json

from .._models import (
    DirectoryEntry as PathBase,
    FileDownload as FileDownloadResponse,
    AppRoutersUtilsModelsStatus as FileDownloadResponseStatus,
    DirectoryOutput as DirectoryListingResponse,
    AppRoutersUtilsModelsStatus as DirectoryListingResponseStatus,
    UploadResult as UploadResponse,
    AppRoutersUtilsModelsStatus as UploadResponseStatus,
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
        remote_path = RemotePath(str(self._path / key))
        # We have to set the compute field separately otherwise
        # we run into ForwardRef issue because of circular deps
        remote_path.compute = self.compute

        return remote_path

    def __rtruediv__(self, key):
        remote_path = RemotePath(str(key / self._path))
        # We have to set the compute field separately otherwise
        # we run into ForwardRef issue because of circular deps
        remote_path.compute = self.compute

        return remote_path

    def __str__(self):
        return str(self._path)

    @property
    def parent(self):
        parent_path = RemotePath(str(self._path.parent))
        # We have to set the compute field separately otherwise
        # we run into ForwardRef issue because of circular deps
        parent_path.compute = self.compute

        return parent_path

    @property
    def parents(self):
        parents = [RemotePath(str(p)) for p in self._path.parents]

        # We have to set the compute field separately otherwise
        # we run into ForwardRef issue because of circular deps
        def _set_compute(p):
            p.compute = self.compute
            return p

        parents = map(_set_compute, parents)

        return parents

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


    def dict(self, *args, **kwargs) -> Dict:
        if "exclude" not in kwargs:
            kwargs["exclude"] = {"compute"}
        return super().dict(*args, **kwargs)

    def is_dir(self):
        if self.perms is None:
            self.update()

        return self.perms[0] == "d"

    def is_file(self):
        return not self.is_dir()

    def download(self, binary=False) -> IO[AnyStr]:
        if self.is_dir():
            raise IsADirectoryError(self._path)

        r = self.compute.client.get(
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
    def _ls(compute: "Compute", path, directory=False) -> List["RemotePath"]:
        r = compute.client.get(f"utilities/ls/{compute.name}/{path}")

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
                if not directory and entry.name in [".", ".."]:
                    continue
                # If we are just listing the directory look for .
                # and just return it. In the future we should look
                # at adding a directory option to the API to avoid
                # the unnecessary listing.
                elif directory and entry.name == ".":
                    entry.name = PurePosixPath(path).name
                    return [_to_remote_path(path, entry)]

                paths.append(_to_remote_path(f"{path}/{entry.name}", entry))

        return paths

    def ls(self) -> List["RemotePath"]:
        return self._ls(self.compute, str(self._path))

    def update(self):
        file_state = self.ls()
        if len(file_state) != 1:
            raise FileNotFoundError(self._path)

        self._update(file_state[0])

    def _update(self, new_file_state: "RemotePath") -> "RemotePath":
        for k in new_file_state.__fields_set__:
            v = getattr(new_file_state, k)
            setattr(self, k, v)

        return self

    def upload(self, file: BytesIO) -> "RemotePath":
        if self.is_dir():
            upload_path = f"{str(self._path)}/{file.filename}"
        else:
            upload_path = str(self._path)

        url = f"utilities/upload/{self.compute.name}/{upload_path}"
        files = {"file": file}

        r = self.compute.client.put(url, files=files)

        json_response = r.json()
        upload_response = UploadResponse.parse_obj(json_response)
        if upload_response.status == UploadResponseStatus.ERROR:
            raise SfApiError(upload_response.error)

        remote_path = RemotePath(upload_path)
        remote_path.compute = self.compute

        return remote_path
