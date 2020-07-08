import pytest
import os
from pathlib import Path
from get_manually_entities import get_all_entity

import barely_db
from barely_db import *


def test_db_load():
    path_fn = Path(__file__).parent.joinpath('Database')
    bdb = BarelyDB(base_path=path_fn, path_depth=1)
    bdb.load_entities()

    filename = os.path.abspath(__file__)
    path_to_fn = Path(os.path.dirname(filename))
    path_to_db = path_to_fn.joinpath('Database')
    all_entities_names = get_all_entity(path_to_db, 'name')

    assert len(bdb.entities) == len(all_entities_names)
