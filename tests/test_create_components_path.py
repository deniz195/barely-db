import pytest
import os
import warnings
import shutil
from pathlib import Path

import barely_db
from barely_db import *


def test_create_entity(bdb):   
    web = bdb.get_entity('WB9042')

    try:
        existing_path = web.entity_path
        shutil.rmtree(existing_path, ignore_errors=True)
        assert(not existing_path.exists())
    except KeyError:
        # if path does not exists keep going
        pass

    # with pytest.deprecated_call():
    new_entity = bdb.create_new_entity(after=web.buid_with_component, name='great_web')
    new_entity_path = new_entity.path
    assert(new_entity_path.exists())

    new_entity_path = web.entity_path
    assert(new_entity_path.exists())

    shutil.rmtree(new_entity_path, ignore_errors=True)
    bdb.load_entities()

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
    ent.create_component(component='P1', name='cool_component')

    component_name ='T1'
    component_comment = 'some_component'
    folder = 'barely-db://Webs/WB3001_SL'
    folder_path = Path(bdb.resolved_file(folder))

    contains_component,path_to_component = check_folder_contains_component(folder_path, component_name)
    if contains_component:
        shutil.rmtree(path_to_component, ignore_errors=True)

    contains_component,path_to_component = check_folder_contains_component(folder_path, component_name)
    assert(not contains_component)

    ent.create_component(component=component_name, name=component_comment)

    contains_component,path_to_component = check_folder_contains_component(folder_path, component_name)
    assert(contains_component)

    os.rmdir(path_to_component)

    contains_component,path_to_component = check_folder_contains_component(folder_path, component_name)
    assert(not contains_component)



    
    
