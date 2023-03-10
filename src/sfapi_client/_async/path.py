from pathlib import PurePosixPath
from pydantic import PrivateAttr

from .._models import DirectoryEntry as PathBase


class RemotePath(PathBase):
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
        return self._path.parent

    @property
    def parents(self):
        return self._path.parents

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