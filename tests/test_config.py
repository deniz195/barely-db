import pytest
import os
import cattr
import warnings
import shutil
from pathlib import Path

import barely_db
from barely_db import *



def test_config_restructure():
    ### Test restructuring
    config = BarelyDBConfig()
    self_dict = cattr.unstructure(config)

    config2 = cattr.structure(self_dict, BarelyDBConfig)
    assert config2 == config


    
def test_config_saveload(scratch_base_path):
    ### Test save and reload
    base_path = scratch_base_path

    config = BarelyDBConfig.from_legacy_default()   
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

    sys_config = BarelyDBSystemConfig.from_legacy_default()   
    sys_config.save(config_file=filename)

    sys_config2 = BarelyDBSystemConfig.load(filename)
    assert sys_config2 == sys_config



