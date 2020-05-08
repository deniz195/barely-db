import logging
import collections
import typing
import attr
import cattr


import datetime
import sys
import os
import copy

import json
import re
from pathlib import Path, PureWindowsPath

from collections import OrderedDict
from collections.abc import Sequence, Container

# from .tools import *
# Naming conventions: https://swift.org/documentation/api-design-guidelines/#strive-for-fluent-usage

__all__ = ['BarelyDBConfig', 'BarelyDBSystemConfig']

# create logger
module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.DEBUG)


# general useful module components
def _reload_module():
    import sys
    import importlib
    current_module = sys.modules[__name__]
    module_logger.info('Reloading module %s' % __name__)
    importlib.reload(current_module)


@attr.s(frozen=True, kw_only=True)
class BarelyDBSystemConfig:
    default_base_path = attr.ib(factory=dict, type=typing.Dict[str, typing.List[str]])

    @classmethod
    def get_file(cls):
        filename = '.bdb_system_config.json'

        user_config_file = str(Path.home().joinpath(filename))
        return user_config_file

    def save(self, config_file=None):
        if config_file is None:
            config_file = self.get_file()        

        self_dict = attr.asdict(self)

        with open(config_file, 'w') as f:
            json.dump(self_dict, f, indent=4)

    @classmethod
    def load(cls, config_file=None, default_to_empty=False):
        if config_file is None:
            config_file = cls.get_file()        

        try:
            with open(config_file, 'rb') as f:
                self_dict = json.load(f)

            return cattr.structure(self_dict, cls)
        
        except FileNotFoundError as e:
            if default_to_empty:
                module_logger.warning(f'Could not load {config_file}!')
                return cls()
            else:
                raise
        


@attr.s(frozen=True, kw_only=True)
class BarelyDBConfig:

    name = attr.ib(default='master', type=str)

    path_depth = attr.ib(default=0)
    known_bases = attr.ib(factory=list, type=typing.List[str])
    ignored_files = attr.ib(factory=list, type=typing.List[str])
    auto_reload_components = attr.ib(default=None)
    buid_types = attr.ib(factory=dict, type=typing.Dict[str, str])

    @staticmethod
    def resolve_file(base_path):
        base_path = Path(base_path)
        
        if base_path.is_dir():
            config_file = base_path.joinpath('bdb_config.json')
        else:
            config_file = base_path

        return str(config_file)

    def save(self, base_path, create_path=False):
        base_path = Path(base_path)
        
        if create_path:
            base_path.mkdir(parents=True, exist_ok=True)

        config_file = self.resolve_file(base_path)
        
        self_dict = attr.asdict(self)

        with open(config_file, 'w') as f:
            json.dump(self_dict, f, indent=4)

    @classmethod
    def load(cls, base_path):
        config_file = Path(cls.resolve_file(base_path))

        with open(config_file, 'rb') as f:
            self_dict = json.load(f)

        return cattr.structure(self_dict, cls)

    