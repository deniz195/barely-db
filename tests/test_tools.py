import pytest
import os
from pathlib import Path

import attr
import cattr

from ruamel.yaml import YAML, yaml_object
from ruamel.yaml.compat import StringIO

import barely_db
from barely_db import *
from barely_db.tools import *


def test_checker(bdb):

    bc = BarelyDBChecker(bdb)
