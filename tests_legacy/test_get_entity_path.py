import pytest
import os
from pathlib import Path

import barely_db
from barely_db import *
from get_manually_entities import get_all_entity

def test_get_entity_path(bdb):
    db_entity_paths = bdb.entity_paths
    
    filename = os.path.abspath(__file__)
    path_to_fn = Path(os.path.dirname(filename))
    path_to_db = path_to_fn.joinpath('Database')
    all_entity_paths = get_all_entity(path_to_db,'paths')

    assert(len(db_entity_paths)==len(all_entity_paths))
    counter = 0
    for entity in db_entity_paths:
        path = str(db_entity_paths[entity])
        assert(path == all_entity_paths[counter])
        counter += 1


