import pytest
import os
from pathlib import Path

path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_file = Path(path_to_file)
db   = path_to_file.joinpath('..','barely-db')

import sys
sys.path.append('..')
sys.path.insert(0, os.fspath(db))


import barely_db
from barely_db import *


### initialize code and database

bdb_local = BarelyDB(base_path='./Database', path_depth=1)
bdb_local.load_entities()
bdb_local.get_code_paths(add_to_sys_path=True)

# Testing mode database
@pytest.fixture(scope="session")
def bdb():
    ''' Creates a barelydb instance using the test database. '''
    return bdb_local

