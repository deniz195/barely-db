import pytest
import os
from pathlib import Path
import attr

import barely_db
from barely_db import file_management, serialize_to_file
from shutil import copyfile

from unitdoc import UnitDocRegistry
udr = UnitDocRegistry()

@serialize_to_file(base_file_identifier='test_class_c', suffix='.yaml')
@udr.serialize()
@attr.s(frozen=True, kw_only=True)
class C():
    name = attr.ib()
    x = udr.attrib(default='1m')

def test_save_to_file(bdb):
    
    web = bdb.get_entity('WB3001')
    web_path= web.get_entity_path()
    before = [f for f in os.listdir(web_path.joinpath('bdb_old'))]
    for i in range(6):
        some_ob = C(name=('object'+str(i)))
        fn_obj = web.save_object(some_ob)
        assert(Path(fn_obj).exists())
    
    after = [f for f in os.listdir(web_path.joinpath('bdb_old'))]
    assert(len(before)==len(after)-6)

    
















