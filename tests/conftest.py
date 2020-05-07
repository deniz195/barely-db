import pytest
import os
from pathlib import Path

repo_base = Path(__file__).absolute().resolve().parent.parent
# db = repo_base.joinpath('..','barely-db').resolve()

print(str(repo_base))

import sys
sys.path.append('..')
sys.path.insert(0, str(repo_base))
# sys.path.insert(0, str(db))


import barely_db
from barely_db import *


### initialize code and database

bdb_local = BarelyDB(base_path='./Database', path_depth=1)
bdb_local.load_entities()

# Testing mode database
@pytest.fixture(scope="session")
def bdb():
    ''' Creates a barelydb instance using the test database. '''
    return bdb_local


# Testing customized BUIDParser
@pytest.fixture(scope="session")
def CBUIDParser():
    ''' Creates a customized BUIDParser. '''
    buid_types = {
        "slurry": "SL",
        "web": "WB",
        "cells": "CL",
        "electrochemistry": "EE",
        "rawmaterial": "RM",
        "experiment": "EXP",
        "equipment": "EQ",
        "manufacturing_orders": "MO",
        "product": "PD",
        "documents": "DOC"
    }

    CBUIDParser = barely_db.BUIDParser.create_class(buid_types)

    return CBUIDParser


