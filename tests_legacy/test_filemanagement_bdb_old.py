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
    
    web = bdb.get_entity('WB9002')
    web_path= web.get_entity_path()
    try:
        before = [f for f in os.listdir(web_path.joinpath('.bdb_old'))]
    except FileNotFoundError:
        before = []

    no_revisions = 6

    some_ob = C(name=('object'+str(0)))
    fn = C.get_serialization_filename(web)

    if Path(fn).exists():
        expected_revisions = no_revisions
    else:
        expected_revisions = no_revisions -1

    for i in range(no_revisions):
        some_ob = C(name=('object'+str(i)))
        fn_obj = web.save_object(some_ob)
        assert(Path(fn_obj).exists())
    
    after = [f for f in os.listdir(web_path.joinpath('.bdb_old'))]
    assert(len(before)==len(after)-expected_revisions)

    
















