import pytest
import os
from pathlib import Path

import barely_db
from barely_db import *


def test_db_resolve_filename(bdb):
    # check which OS it is
    # depending on OS different test
    if os.name.lower == "posix":
        fn = '/Volumes/GoogleDrive/Teamablagen/Database/Webs/WB3001_SL_LGA1/-P1/raw_peelforce/P1-BE_peelforce_190411.tsv.plot.png'
    else:
        fn = 'G:\\My Drive\\Battrion_AG\\DATABASE\\Webs\\WB3001_SL_LGA1\\-P1\\raw_peelforce\\P1-BE_peelforce_190411.tsv.plot.png'
    fn_r = bdb.resolve_file(fn)     
    assert(Path(fn_r).exists())
    
    fn = 'barelydb://Webs/WB3001_SL_LGA1/-P1/raw_peelforce/P1-BE_peelforce_190411.tsv.plot.png'
    fn_r = bdb.resolve_file(fn)     
    assert(Path(fn_r).exists())

    fn = 'barelydb://Webs/WB3001_SL_LGA1/-P1/raw_peelforce/P1-BE_peelforce_190411.tsv.plot.png'
    fn_rel = bdb.relative_file(fn)     
    assert(fn_rel == 'Webs/WB3001_SL_LGA1/-P1/raw_peelforce/P1-BE_peelforce_190411.tsv.plot.png')

    fn_abs = bdb.absolute_file(fn_rel)     
    assert(Path(fn_abs).exists())

    with pytest.raises(ValueError):
        fn_abs = bdb.absolute_file('../lala.yaml')     
    

