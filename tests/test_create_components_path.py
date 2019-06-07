import pytest
import os
import warnings
from pathlib import Path

import barely_db
from barely_db import *

def test_create_components(bdb):
    ent = bdb.get_entity('WB3001')
    with pytest.deprecated_call():
        ent.create_component_path('P1')
    
    ent.create_component_path('T1')
    folder = 'barely-db://Webs/WB3001_SL_LGA1'
    folder_path = Path(bdb.resolve_file(folder))
    contains_new_component = False
    path_new_component =''
    for file in os.listdir(folder_path):
        if 'T1' in file:
            contains_new_component= True
            path_new_component = folder_path.joinpath(file)
            break
    assert(contains_new_component)
    os.rmdir(path_new_component)
    contains_new_component = False
    for file in os.listdir(folder_path):
            if 'T1' in file:
                contains_new_component= True
                break
    assert(not contains_new_component)


    
    