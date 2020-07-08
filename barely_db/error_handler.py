import logging
import os
import sys

from pathlib import Path

__all__ = ['DefaultErrorHandler']


class DefaultErrorHandler(object):
    def __init__(self, suppress_exception=False):
        self._filename = None
        self._target_cls = None
        self.file_path_cls_def = None
        self.suppress_exception = suppress_exception
        self.logger = logging.getLogger(self.__class__.__qualname__)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, traceback):
        return self.suppress_exception

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, fn):
        self._filename = Path(fn)

    @property
    def target_cls(self):
        return self._target_cls

    @target_cls.setter
    def target_cls(self, cls):
        self._target_cls = cls
        try:
            self.file_path_cls_def = Path(os.path.abspath(sys.modules[cls.__module__].__file__))
        except BaseException:
            self.file_path_cls_def = None
