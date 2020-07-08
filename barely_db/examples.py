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

import shutil
import names
from random_words import RandomWords

from . import *

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


def make_example_db(base_path):

    rw = RandomWords()

    if Path(BarelyDBConfig.resolve_file(base_path)).exists():
        module_logger.warning(f'Removing existing {base_path}')
        shutil.rmtree(str(base_path))

    bdb_config = BarelyDBConfig(
        name='bakery',
        path_depth=1,
        buid_types={
            'ingrediences': 'IG',
            'doughs': 'DG',
            'breads': 'BR',
            'equipment': 'EQ',
            'customers': 'CU',
            'documents': 'DOC',
        },
    )

    bdb_config.save(base_path, create_path=True)

    bdb = BarelyDB(base_path=base_path)
    # bdb.load_entities()

    for x, bt in bdb.config.buid_types.items():
        p = bdb.base_path.joinpath(x)
        p.mkdir(exist_ok=True)
        bdb.buid_type_paths[bt] = str(p)

    for i in range(0, 20):
        bdb.create_new_entity(after='CU0001', name=names.get_full_name(), reload=False)

    for name in ['mixer_30L', 'mixer_5L', 'sieve', 'scale_30kg']:
        ent = bdb.create_new_entity(after='EQ0001', name=name, reload=False)
        ent.create_component(component='D1', name='device1')
        ent.create_component(component='D2', name='device2')

    for name in [
        'flour_white_supplierA',
        'flour_white_supplierB',
        'flour_brown_supplierC',
        'water',
        'yeast_supplierK',
        'yeast_supplierJ',
    ]:
        ent = bdb.create_new_entity(after='IG0001', name=name, reload=False)

    buid_types = {'IG': 20, 'DG': 30, 'BR': 30, 'DOC': 10}
    for bt, number in buid_types.items():
        for i in range(0, number):
            bdb.create_new_entity(after=bt + '0001', name=rw.random_word(), reload=False)

    bdb.load_entities()

    return bdb


@serialize_to_file(base_file_identifier='dough_recipe.json')
@cattr_json_serialize
@attr.s(frozen=True, kw_only=True)
class DoughRecipe:
    water = attr.ib(default='IG0004-B1')
    flour = attr.ib(default='IG0001-B1')

    w_water = attr.ib(default='1kg')
    w_flour = attr.ib(default='1kg')
