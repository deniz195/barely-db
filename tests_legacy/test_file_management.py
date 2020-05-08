import pytest
import os
from pathlib import Path

import attr
import cattr

from ruamel.yaml import YAML, yaml_object
from ruamel.yaml.compat import StringIO

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


yaml_parser = YAML()

def add_yaml_serialize():
    cattr_converter = cattr.global_converter
    yaml = yaml_parser
    def decorate_class(cls):
        def to_yaml(obj):
            stream = StringIO()
            yaml_parser.dump(cattr_converter.unstructure(obj), stream)
            return stream.getvalue()
    
        def from_yaml(raw_yaml):
            return cattr_converter.structure(yaml_parser.load(raw_yaml), cls)
        
        cls.serialize = to_yaml
        cls.deserialize = from_yaml
        return cls
    
    return decorate_class




def test_serialize_to_file(bdb):

    @add_yaml_serialize()
    @attr.s()
    class Xbase(object):
        a = attr.ib(default='Hello')
        b = attr.ib(default='Hello I\'m b')


    x1 = Xbase()
    print(x1.serialize())

    test_ent = bdb.get_entity('WB9001-Y9')
    base_path = test_ent.get_component_path()
    print(base_path)

    fm = test_ent.make_file_manager()
    all_fns = fm.get_files('*', files_only=True)
    print(f'removing {all_fns}')
    for fn in all_fns:
        os.remove(fn)

    @serialize_to_file(base_file_identifier=None, 
                        prepend_buid=False, 
                        prefix='', suffix='.UHHH.yaml',
                        serialize_method = 'serialize', deserialize_classmethod = 'deserialize',
                        allow_parent=False, binary=False,)
    class X1(Xbase):
        pass

    x1 = X1()

    fn = fm.make_export_file_name('LALALA')
    print(fn)
    assert(not Path(fn).exists())
    
    x1.save_to_file(fn)
    assert(Path(fn).exists())

    with pytest.raises(ValueError, match='No file_identifier given.'):
        fn = x1.save_to_entity(test_ent)

    fn = x1.save_to_entity(test_ent, file_identifier='LALA')
    assert('LALA.UHHH.yaml' == Path(fn).name)
    assert(x1.file_serializer.match_filename(fn, ))
    assert(x1.file_serializer.match_filename(fn, file_identifier='LALA'))
    assert(Path(fn).exists())


    @serialize_to_file('some_data_X2.yaml')
    class X2(Xbase):
        pass

    x2 = X2()
    fn = x2.save_to_entity(test_ent)
    assert('some_data_X2.yaml' == Path(fn).name)
    assert(x2.file_serializer.match_filename(fn, ))
    assert(Path(fn).exists())

    fn = x2.save_to_entity(test_ent, file_identifier='MANA')
    assert('MANA' == Path(fn).name)
    assert(x2.file_serializer.match_filename(fn, file_identifier='MANA'))
    assert(Path(fn).exists())


    @serialize_to_file('some_data.yaml', prepend_buid=True)
    class X3(Xbase):
        pass

    x3 = X3()
    fn = x3.save_to_entity(test_ent)
    assert('WB9001-Y9_some_data.yaml' == Path(fn).name)
    assert(x3.file_serializer.match_filename(fn))
    assert(Path(fn).exists())


    @serialize_to_file(suffix='.some_data.yaml', prepend_buid=True)
    class X4(Xbase):
        pass

    x4 = X4()
    fn = x4.save_to_entity(test_ent, file_identifier='PALA')
    assert('WB9001-Y9_PALA.some_data.yaml' == Path(fn).name)
    assert(x4.file_serializer.match_filename(fn))
    assert(x4.file_serializer.match_filename(fn, file_identifier='PALA'))
    assert(Path(fn).exists())

    with pytest.raises(ValueError, match='No file_identifier given.'):
        fn = x4.save_to_entity(test_ent)




    ## Test load
    @serialize_to_file('some_data_X5.yaml', prepend_buid=True)
    class X5(Xbase):
        pass

    @serialize_to_file('some_data_X6.yaml', prepend_buid=True)
    class X6(Xbase):
        pass

    x5 = X5()
    fn = x5.save_to_entity(test_ent)
    assert('WB9001-Y9_some_data_X5.yaml' == Path(fn).name)
    assert(x5.file_serializer.match_filename(fn))
    assert(Path(fn).exists())

    assert(test_ent.has_object(X5))
    assert(not test_ent.has_object(X6))
    
    x5_loaded = test_ent.load_object(X5)
    assert(x5_loaded.serialize() == x5.serialize())
