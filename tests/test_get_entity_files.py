import pytest
import os
from pathlib import Path

import barely_db
from barely_db import *


def test_get_entity_files(bdb):
    entity_files_list = bdb.get_entity_files('WB3001', '*')
    folder = 'barely-db://Webs/WB3001_SL_LGA1'
    folder_path = bdb.resolve_file(folder) 
    all_paths = []
    for filename in os.listdir(folder_path):
        all_paths.append(str((Path(folder_path)).joinpath(filename)))

    assert(len(entity_files_list)==len(all_paths))
    
    counter = 0
    for entity_file_path in entity_files_list :
        assert(str(entity_file_path)==all_paths[counter])
        counter +=1
    

