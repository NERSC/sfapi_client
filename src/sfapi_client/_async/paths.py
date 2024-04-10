from typing import Optional, List, IO, AnyStr, Dict, Tuple
from pathlib import PurePosixPath, Path
from pydantic import PrivateAttr
from io import StringIO, BytesIO
from base64 import b64decode
from contextlib import asynccontextmanager
import tempfile

from .._models import (
    DirectoryEntry as PathBase,
    FileDownload as FileDownloadResponse,
    AppRoutersUtilsModelsStatus as FileDownloadResponseStatus,
    DirectoryOutput as DirectoryListingResponse,
    AppRoutersUtilsModelsStatus as DirectoryListingResponseStatus,
    UploadResult as UploadResponse,
    AppRoutersUtilsModelsStatus as UploadResponseStatus,
)
from ..exceptions import SfApiError


def _is_no_such(error: SfApiError):
    return "No such file or directory" in error.message


class AsyncRemotePath(PathBase):
    """
    RemotePath is used to model a remote path, it takes inspiration from
    pathlib and shares some of its interface.
    """

    compute: Optional["AsyncCompute"]  # noqa: F821
    # It would be nice to be able subclass PurePosixPath, however, this
    # require using private interfaces. So we derive by composition.
    _path: PurePosixPath = PrivateAttr()

    def __init__(self, path=None, **kwargs):
        super().__init__(**kwargs)
        self._path = PurePosixPath(path)

        if self.name is None:
            self.name = self._path.name

    def __truediv__(self, key):
        remote_path = AsyncRemotePath(path=str(self._path / key), compute=self.compute)

        return remote_path

    def __rtruediv__(self, key):
        remote_path = AsyncRemotePath(path=str(key / self._path), compute=self.compute)

        return remote_path

    def __str__(self):
        return str(self._path)

    @property
    def parent(self) -> "RemotePath":  # noqa: F821
        """
        The parent of the path.

        :return: the parent

        """
        parent_path = AsyncRemotePath(path=str(self._path.parent), compute=self.compute)

        return parent_path

    @property
    def parents(self) -> List["RemotePath"]:  # noqa: F821
        """
        The parents of the path.

        :return: the parents
        """
        parents = [
            AsyncRemotePath(path=str(p), compute=self.compute)
            for p in self._path.parents
        ]

        return parents

    @property
    def stem(self) -> str:
        """
        The final path component, without its suffix.

        :return: the path stem
        """
        return self._path.stem

    @property
    def suffix(self) -> str:
        """
        The path extension.

        :return: the path extension
        """
        return self._path.suffix

    @property
    def suffixes(self) -> List[str]:
        """
        A list of the path extensions.

        :return: the path extensions
        """
        return self._path.suffixes

    @property
    def parts(self) -> Tuple[str]:
        """
        The paths components as a tuple.

        :return: the path components
        """
        return self._path.parts

    def dict(self, *args, **kwargs) -> Dict:
        if "exclude" not in kwargs:
            kwargs["exclude"] = {"compute"}
        return super().dict(*args, **kwargs)

    async def is_dir(self) -> bool:
        """
        :return: Returns True if path is a directory, False otherwise.
        """
        if self.perms is None:
            await self.update()

        return self.perms[0] == "d"

    async def is_file(self) -> bool:
        """
        :return: Returns True if path is a file, False otherwise.
        """
        return not await self.is_dir()

    async def download(self, binary=False) -> IO[AnyStr]:
        """
        Download the file contents.

        :param binary: indicate if the file should be treated as binary, defaults
        to False
        :raises IsADirectoryError: if path points to a directory.
        :raises SfApiError:
        """
        if await self.is_dir():
            raise IsADirectoryError(self._path)

        r = await self.compute.client.get(
            f"utilities/download/{self.compute.name}/{self._path}?binary={binary}"
        )
        json_response = r.json()
        download_response = FileDownloadResponse.model_validate(json_response)

        if download_response.status == FileDownloadResponseStatus.ERROR:
            raise SfApiError(download_response.error)

        file_data = download_response.file
        if download_response.is_binary:
            binary_file_data = b64decode(file_data)
            return BytesIO(binary_file_data)
        else:
            return StringIO(file_data)

    @staticmethod
    async def _ls(
        compute: "AsyncCompute",  # noqa: F821
        path,
        directory=False,
        filter_dots=True,  # noqa: F821
    ) -> List["RemotePath"]:  # noqa: F821
        r = await compute.client.get(f"utilities/ls/{compute.name}/{path}")

        json_response = r.json()
        directory_listing_response = DirectoryListingResponse.model_validate(
            json_response
        )
        if directory_listing_response.status == DirectoryListingResponseStatus.ERROR:
            raise SfApiError(directory_listing_response.error)

        paths = []

        def _to_remote_path(path, entry):
            kwargs = entry.model_dump()
            kwargs.update(path=path, compute=compute)
            p = AsyncRemotePath(**kwargs)

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
                if filter_dots and not directory and entry.name in [".", ".."]:
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

    async def ls(self) -> List["AsyncRemotePath"]:
        """
        List the current path

        :return: the list of child paths
        """
        return await self._ls(self.compute, str(self._path))

    async def update(self):
        """
        Update the path in the latest information from the resource.
        """
        # Here we pass filter_dots=False so that we with get . if this is a
        # directory
        file_state = await self._ls(self.compute, str(self._path), filter_dots=False)
        if len(file_state) == 0:
            raise FileNotFoundError(self._path)

        # We update the name as it could be . from a directory listing and in that
        # case we don't want to update the name
        new_state = file_state[0]
        new_state.name = self.name

        self._update(new_state)

    def _update(self, new_file_state: "AsyncRemotePath") -> "AsyncRemotePath":
        for k in new_file_state.model_fields_set:
            v = getattr(new_file_state, k)
            setattr(self, k, v)

        return self

    async def upload(self, file: BytesIO) -> "AsyncRemotePath":
        try:
            if await self.is_dir():
                upload_path = f"{str(self._path)}/{file.filename}"
            else:
                upload_path = str(self._path)
        except SfApiError as ex:
            # Its a valid use case to add a upload a new file to an exiting directory.
            # In this case the is_dir() will raise a SfApiError with
            # "No such file or directory" So we check for that and then see if the
            # parent directory exists, if it does we can just continue.
            if not _is_no_such(ex):
                raise

            # Check if the parent is a directory ( as in we are creating a new file ),
            # if not re raise the original exception
            if not await self.parent.is_dir():
                raise
            else:
                upload_path = str(self._path)

        url = f"utilities/upload/{self.compute.name}/{upload_path}"
        files = {"file": file}

        r = await self.compute.client.put(url, files=files)

        json_response = r.json()
        upload_response = UploadResponse.model_validate(json_response)
        if upload_response.status == UploadResponseStatus.ERROR:
            raise SfApiError(upload_response.error)

        remote_path = AsyncRemotePath(path=upload_path, compute=self.compute)

        return remote_path

    @asynccontextmanager
    async def open(self, mode: str) -> IO[AnyStr]:
        """
        Open the file at this path.

        :param mode: The mode to open the file. Valid options are 'rwb'.

        raises: IsDirectoryError: If the path is not a file.
        """
        try:
            if await self.is_dir():
                raise IsADirectoryError()
        except SfApiError as ex:
            # Its a valid use case to add a open a new file to an exiting directory.
            # In this case the is_dir() will raise a SfApiError with
            # "No such file or directory" So we check for that and then see if the
            # parent directory exists, if it does we can just continue.
            if not _is_no_such(ex):
                raise

            # Check if the parent is a directory ( as in we are creating a new file ),
            # if not re raise the original exception
            if not await self.parent.is_dir():
                raise

        valid_modes_chars = set("rwb")
        mode_chars = set(mode)

        # If we have duplicate raise exception
        if len(mode_chars) != len(mode):
            raise ValueError(f"invalid mode: '{mode}'")

        # check mode chars
        if not mode_chars.issubset(valid_modes_chars):
            raise ValueError(f"invalid mode: '{mode}'")

        # we don't support read/write
        if "r" in mode_chars and "w" in mode_chars:
            raise ValueError(f"invalid mode: '{mode}', 'rw' not supported.")

        if "r" in mode_chars:
            binary = "b" in mode_chars
            yield await self.download(binary)
        else:
            tmp = None
            try:
                tmp = tempfile.NamedTemporaryFile(mode, delete=False)
                yield tmp
                tmp.close()
                # Now upload the changes, we have to reopen the file to
                # ensure binary mode
                with open(tmp.name, "rb") as fp:
                    await self.upload(fp)
            finally:
                if tmp is not None:
                    tmp.close()
                    Path(tmp.name).unlink()
