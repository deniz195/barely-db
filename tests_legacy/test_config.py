import pytest
import os
import cattr
import warnings
import shutil
from pathlib import Path

import barely_db
from barely_db import *
from barely_db.legacy import *



def test_config_restructure():
    ### Test restructuring
    config = BarelyDBConfig()
    self_dict = cattr.unstructure(config)

    config2 = cattr.structure(self_dict, BarelyDBConfig)
    assert config2 == config


    
def test_config_saveload(scratch_base_path):
    ### Test save and reload
    base_path = scratch_base_path

    config = LegacyDefaultBarelyDBConfig()
    config.save(base_path=base_path)

    config2 = BarelyDBConfig.load(base_path)
    assert config2 == config



def test_sys_config_restructure():
    ### Test restructuring
    sys_config = BarelyDBSystemConfig()
    self_dict = cattr.unstructure(sys_config)

    sys_config2 = cattr.structure(self_dict, BarelyDBSystemConfig)
    assert sys_config2 == sys_config


    
def test_sys_config_saveload(scratch_base_path):
    ### Test save and reload
    filename = str(Path(scratch_base_path).joinpath('temp_bdb_sysconig.json'))

    sys_config = LegacyDefaultBarelyDBSystemConfig()
    sys_config.save(config_file=filename)

    sys_config2 = BarelyDBSystemConfig.load(filename)
    assert sys_config2 == sys_config





def test_empty_db(scratch_base_path):
    base_path = scratch_base_path

    bdb_config = BarelyDBConfig(name='bakery', path_depth=1, 
                   buid_types={\
                        'ingrediences': 'IG',
                        'doughs': 'DG',
                        'breads': 'BD',
                        'customers': 'CU',
                        'documents': 'DOC',
                              })

    bdb_config.save(base_path, create_path=True)
    
    bdb = BarelyDB(base_path=base_path)
    bdb.load_entities()        


    