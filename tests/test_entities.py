import pytest
import os
from pathlib import Path
import re

import barely_db
from barely_db import *
from get_manually_entities import get_all_entity


def test_components(bdb):

    ent = bdb.get_entity('WB9001-Y9')
    assert ent.buid_with_component == 'WB9001-Y9'
    assert ent.buid_entity == 'WB9001'
    assert ent.buid == 'WB9001'

    assert ent.path == ent.component_path
    assert ent.path == ent.component_paths['Y9']
    assert 'Y9' in ent.components

    assert str(ent.entity_path) in str(ent.path)

    assert ent.entity_path == ent.parent.path
    assert ent.entity_path == ent.parent.entity_path
    assert ent.entity_path == ent.parent.parent.path

    assert ent.parent == ent.parent.parent

    ent = bdb.get_entity('WB9001')
    assert ent == ent.parent


def test_eq_entities(bdb):
    web = bdb.get_entity('WB3001')
    web_1 = bdb.get_entity('WB0303')

    assert not (web == web_1)
    assert web == web


def test_entity_files(bdb):
    ent = bdb['WB3001']

    assert ent.name == 'SL'

    entity_files_list = ent.files('*')

    folder = 'barely-db://Webs/WB3001_SL'
    folder_path = bdb.resolved_file(folder)
    all_paths = []
    for filename in os.listdir(folder_path):
        all_paths.append(str((Path(folder_path)).joinpath(filename)))

    assert len(entity_files_list) == len(all_paths)

    counter = 0
    for entity_file_path in entity_files_list:
        assert str(entity_file_path) == all_paths[counter]
        counter += 1


def test_get_entity_components(bdb):
    bdb_entities_names = bdb.entities

    filename = os.path.abspath(__file__)
    path_to_fn = Path(os.path.dirname(filename))
    path_to_db = path_to_fn.joinpath('Database')
    manual_entities_paths = get_all_entity(path_to_db, 'path')

    assert len(bdb_entities_names) == len(manual_entities_paths)
    counter = 0
    for entity_name in bdb_entities_names:
        ent = bdb[entity_name]

        bdb_entity_components = ent.component_paths
        bdb_entity_components_names = list(bdb_entity_components.keys())
        bdb_entity_components_paths = list(bdb_entity_components.values())

        manual_entity_path = manual_entities_paths[counter]

        comp_regex = r'-([a-zA-Z]{1,2}\d{1,5})(?:[^\d].*)?'

        manual_entity_components = [
            f for f in os.scandir(manual_entity_path) if f.is_dir() and re.match(comp_regex, f.name)
        ]
        manual_entity_components_names = [f.name for f in manual_entity_components]
        manual_entity_components_paths = [f.path for f in manual_entity_components]

        print('Name of bdb: {}'.format(entity_name))
        print('Name taken manually: {}'.format(os.path.basename(manual_entity_path)))
        assert len(bdb_entity_components_names) == len(manual_entity_components_names)
        assert len(bdb_entity_components_paths) == len(manual_entity_components_paths)

        for i in range(len(bdb_entity_components_names)):
            assert bdb_entity_components_names[i] in manual_entity_components_names[i]
            assert str(bdb_entity_components_paths[i]) == manual_entity_components_paths[i]

        counter += 1


def test_get_entity_path(bdb):
    db_entity_paths = bdb.entity_paths

    filename = os.path.abspath(__file__)
    path_to_fn = Path(os.path.dirname(filename))
    path_to_db = path_to_fn.joinpath('Database')
    all_entity_paths = get_all_entity(path_to_db, 'paths')

    assert len(db_entity_paths) == len(all_entity_paths)
    counter = 0
    for entity in db_entity_paths:
        path = str(db_entity_paths[entity])
        assert path == all_entity_paths[counter]
        counter += 1
