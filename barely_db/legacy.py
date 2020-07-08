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

# from .file_management import FileManager, FileNameAnalyzer, serialize_to_file, open_in_explorer
from .configs import *
from .parser import *
from .file_management import *


__all__ = ['LegacyDefaultBarelyDBSystemConfig', 'LegacyDefaultBarelyDBConfig']

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


def LegacyDefaultBarelyDBSystemConfig():
    return BarelyDBSystemConfig(
        default_base_path={
            'battrion_manufacturing': [
                'G:\\Team Drives\\Database',
                'G:\\Shared drives\\Database',
                '/Volumes/GoogleDrive/Team Drives/Database',
                '/Volumes/GoogleDrive/Teamablagen/Database',
                '/Volumes/GoogleDrive/Geteilte Ablagen/Database',
                'G:\\Geteilte Ablagen\\Database',
                'G:\\Drive partagés\\Database',
                '/home/pi/GoogleDrive/database',
                '/home/jovyan/database',
            ]
        }
    )


def LegacyDefaultBarelyDBConfig():
    return BarelyDBConfig(
        name='battrion_manufacturing',
        path_depth=1,
        known_bases=[
            'G:\\My Drive\\Battrion_AG\\DATABASE\\',
            'G:\\Team Drives\\Database\\',
            'G:\\Shared drives\\Database\\',
            'G:\\Geteilte Ablagen\\Database\\',
            'G:\\Drive partagés\\Database\\',
            '/home/pi/GoogleDrive/database/',
            '/home/jovyan/database/',
            'barelydb://',
            'barely-db://',
        ],
        ignored_files=['desktop.ini'],
        auto_reload_components=None,
        buid_types={
            'slurry': 'SL',
            'web': 'WB',
            'cells': 'CL',
            'electrochemistry': 'EE',
            'rawmaterial': 'RM',
            'experiment': 'EXP',
            'equipment': 'EQ',
            'manufacturing_orders': 'MO',
            'product': 'PD',
            'documents': 'DOC',
        },
    )
