import pytest
import os
import warnings
import shutil
from pathlib import Path

import barely_db
from barely_db import *

def check_folder_contains_component(folder_path, component_name):
    contains_component = False
    path_to_component =''
    for file in os.listdir(folder_path):
        if component_name in file:
            contains_component= True
            path_to_component = folder_path.joinpath(file)
            break
    return contains_component, path_to_component

def test_create_components(bdb):
    
    ent = bdb.get_entity('WB3001')
    with pytest.deprecated_call():
        ent.create_component_path('P1')

    component_name ='T1'
    folder = 'barely-db://Webs/WB3001_SL_LGA1'
    folder_path = Path(bdb.resolve_file(folder))

    contains_component,path_to_component = check_folder_contains_component(folder_path, component_name)
    if contains_component:
        shutil.rmtree(path_to_component, ignore_errors=True)

    contains_component,path_to_component = check_folder_contains_component(folder_path, component_name)
    assert(not contains_component)

    ent.create_component_path(component_name)

    contains_component,path_to_component = check_folder_contains_component(folder_path, component_name)
    assert(contains_component)

    os.rmdir(path_to_component)

    contains_component,path_to_component = check_folder_contains_component(folder_path, component_name)
    assert(not contains_component)



    
    
