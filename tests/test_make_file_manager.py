import pytest
import os
from pathlib import Path

import barely_db
from barely_db import *
from get_manually_entities import get_all_entity

def test_filemanager(bdb):
    ent = bdb.get_entity('WB3001')

    fm = ent.make_file_manager()
    
    fns = fm.get_files('*.yaml')
    assert(len(fns) == 3)

    fns = fm.get_files('*', directories_only=True)
    assert(len(fns) == 2)

    fns = fm.get_directories('*')
    assert(len(fns) == 2)

    fns = fm.get_files('lalalalala_does_not_exist')
    assert(len(fns) == 0)

    fns = fm.get_directories('lalalalala_does_not_exist')
    assert(len(fns) == 0)

