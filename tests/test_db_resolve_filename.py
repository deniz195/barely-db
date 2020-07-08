import pytest
import os
from pathlib import Path

import barely_db
from barely_db import *


def test_resolved_filename(bdb):
    fn_rel = 'Webs/WB3001_SL/-P1/raw_peelforce/P1-BE_peelforce_190411.tsv.plot.png'
    fn_ref = str(bdb.base_path.joinpath(fn_rel))

    assert bdb.absolute_file(fn_rel) == fn_ref

    fn = (
        'G:\\My Drive\\Battrion_AG\\DATABASE\\Webs\\WB3001_SL\\-P1\\raw_peelforce\\P1-BE_peelforce_190411.tsv.plot.png'
    )
    assert bdb.resolved_file(fn) == fn_ref

    fn = '/Volumes/GoogleDrive/Teamablagen/Database/Webs/WB3001_SL/-P1/raw_peelforce/P1-BE_peelforce_190411.tsv.plot.png'
    assert bdb.resolved_file(fn) == fn_ref

    fn = 'barely-db://Webs/WB3001_SL/-P1/raw_peelforce/P1-BE_peelforce_190411.tsv.plot.png'
    assert bdb.resolved_file(fn) == fn_ref

    with pytest.raises(ValueError):
        fn_abs = bdb.absolute_file('../lala.yaml')
