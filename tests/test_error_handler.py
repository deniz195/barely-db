import pytest
import os
from pathlib import Path
from get_manually_entities import get_all_entity

import barely_db
from barely_db import BarelyDB, serialize_to_file
from barely_db.error_handler import DefaultErrorHandler


def test_error_handler():
    path_fn = Path(__file__).parent.joinpath('Database')
    bdb = BarelyDB(base_path=path_fn, path_depth=1)
    bdb.load_entities()

    my_error_handlers = [None, DefaultErrorHandler()]

    @serialize_to_file(base_file_identifier='test_error.yaml')
    class TestErrorClass:
        @classmethod
        def deserialize(cls, data):
            raise RuntimeError('This class raises an exception when deserialized')

    @serialize_to_file(base_file_identifier='test_error.yaml')
    class TestNoErrorClass:
        @classmethod
        def deserialize(cls, data):
            return 42

    web = bdb['WB3001']

    for my_error_handler in my_error_handlers:
        bdb.register_error_handler(my_error_handler)

        with pytest.raises(RuntimeError, match='This class raises an exception when deserialized'):
            tec = TestErrorClass.load_from_entity(web)

        with pytest.raises(RuntimeError, match='This class raises an exception when deserialized'):
            tec = web.load_object(TestErrorClass, fail_to_exception=True)

        with pytest.raises(RuntimeError, match='This class raises an exception when deserialized'):
            # fail_to_exception = False does only capture file not found errors
            tec = web.load_object(TestErrorClass, fail_to_exception=False)

        tnec = web.load_object(TestNoErrorClass, fail_to_exception=False)
        assert tnec == 42
