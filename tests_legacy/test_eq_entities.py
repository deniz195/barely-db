import pytest
import os
from pathlib import Path

import barely_db
from barely_db import * 


def test_eq_entities(bdb):
    web = bdb.get_entity('WB3001')
    web_1 = bdb.get_entity('WB0303')

    assert(not (web == web_1))
    assert(web == web)

    