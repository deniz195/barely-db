import pytest
import os
from pathlib import Path
import re

import barely_db
from barely_db import *
from get_manually_entities import get_all_entity

def test_get_entity_components(bdb):
    bdb_entities_names = bdb.entities

    filename = os.path.abspath(__file__)
    path_to_fn = Path(os.path.dirname(filename))
    path_to_db = path_to_fn.joinpath('Database')
    manual_entities_paths = get_all_entity(path_to_db,'path')
    
    assert(len(bdb_entities_names)== len(manual_entities_paths))
    counter = 0
    for entity_name in bdb_entities_names:
        ent = bdb.get_entity(entity_name)

        bdb_entity_componentens= ent.get_component_paths()
        bdb_entity_componentens_names = list(bdb_entity_componentens.keys())
        bdb_entity_componentens_paths = list(bdb_entity_componentens.values())

        manual_entity_path = manual_entities_paths[counter]
        
        comp_regex = r'-([a-zA-Z]{1,2}\d{1,5})(?:[^\d].*)?'
            
        manual_entity_componentens= [f for f in os.scandir(manual_entity_path) if f.is_dir() and re.match(comp_regex, f.name)]
        manual_entity_componentens_names= [f.name for f in manual_entity_componentens]
        manual_entity_componentens_paths= [f.path for f in manual_entity_componentens]
        
        print('Name of bdb: {}'.format(entity_name))
        print('Name taken manually: {}'.format(os.path.basename(manual_entity_path)))
        assert(len(bdb_entity_componentens_names)==len(manual_entity_componentens_names))
        assert(len(bdb_entity_componentens_paths)==len(manual_entity_componentens_paths))

        for i in range(len(bdb_entity_componentens_names)):
            assert(bdb_entity_componentens_names[i] in manual_entity_componentens_names[i])
            assert(str(bdb_entity_componentens_paths[i])==manual_entity_componentens_paths[i])


        counter +=1
