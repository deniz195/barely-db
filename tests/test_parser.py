import pytest
import os
import warnings
import shutil
from pathlib import Path

import barely_db
from barely_db import *



def test_parser_basic():
    buid_p = BUIDParser(ignore_unknown=True, mode = 'unique')

    # aa = BUID(buid_p('XasfwX_sl293__Y'))
    # print(repr(aa))
    # print(str(aa))

    def _test_normalization(s, result=None):
        buid = buid_p.parse(s)       
        print(f'{s} --> {buid}')
        # if result is not None:
        assert(buid == result)

    print(f'Normal BUID parsing:')
    _test_normalization('XasfwX_sl293_sl293__Y', 'SL0293')
    _test_normalization('XasfwX_sl293_sl333__Y', None)
    _test_normalization('lorem ipsum', None)
    _test_normalization('SL000293', 'SL0029')
    _test_normalization('WB0251', 'WB0251')
    _test_normalization('WB0252-D2', 'WB0252-D2')
    _test_normalization('WB0252-AFD2', 'WB0252')
    _test_normalization('WB0252-AFD21231451', 'WB0252')  
                  
    def _test_components(s, result=None):
        buid = buid_p.parse_component(s)
        print(f'{s} --> {buid}')
        # if result is not None:
        assert(buid == result)
                  
    print(f'Only components:')
    _test_components('WB0252-D2', 'D2')
    _test_components('CL0152-N50', 'N50')
    _test_components('WB0252', None)

    buid_p2 = BUIDParser(ignore_unknown=True, mode = 'unique', allow_components = False)

    def _test_normalization(s, result=None):
        buid = buid_p2.parse(s)
        print(f'{s} --> {buid}')
        assert(buid == result)
                  
    print(f'No components:')
    _test_normalization('WB0252-D2', 'WB0252')
    _test_normalization('WB0252', 'WB0252')
              
    def _test_parser_mode(buid_p, result=None):
        s = 'XasfwX_sl293_sl333_dp241_sl333_dp241_Y'
        buid = buid_p(s)
        print(f'{s} --> {buid}')
        assert(buid == result)

    _test_parser_mode(BUIDParser(ignore_unknown=True, mode = 'all'), ['SL0293', 'SL0333', 'SL0333'])
    _test_parser_mode(BUIDParser(ignore_unknown=False, mode = 'all'), ['SL0293', 'SL0333', 'DP0241', 'SL0333', 'DP0241'])
    _test_parser_mode(BUIDParser(ignore_unknown=True, mode = 'all_unique'), ['SL0293', 'SL0333'])
    _test_parser_mode(BUIDParser(ignore_unknown=False, mode = 'all_unique'), ['SL0293', 'SL0333', 'DP0241'])
    _test_parser_mode(BUIDParser(ignore_unknown=True, mode = 'first'), 'SL0293')
    _test_parser_mode(BUIDParser(ignore_unknown=True, mode = 'last'), 'SL0333')
    _test_parser_mode(BUIDParser(ignore_unknown=False, mode = 'last'), 'DP0241')
    _test_parser_mode(BUIDParser(ignore_unknown=True, mode = 'unique'), None)

              
    def _test_parser_type(buid_p, result=None):
        s = 'XasfwX_sl293_sl333_dp241_sl333_dp241_Y'
        buid = buid_p.parse_type(s)
        print(f'{s} --> {buid}')
        assert(buid == result)

    _test_parser_type(BUIDParser(ignore_unknown=True, mode = 'all'), ['SL', 'SL', 'SL'])
    _test_parser_type(BUIDParser(ignore_unknown=False, mode = 'all'), ['SL', 'SL', 'DP', 'SL', 'DP'])
    # _test_parser_type(BUIDParser(ignore_unknown=True, mode = 'all_unique'), ['SL']) # NOT CORRECTLY IMPLEMENTED YET!
    # _test_parser_type(BUIDParser(ignore_unknown=False, mode = 'all_unique'), ['SL', 'DP']) # NOT CORRECTLY IMPLEMENTED YET!
    _test_parser_type(BUIDParser(ignore_unknown=True, mode = 'first'), 'SL')
    _test_parser_type(BUIDParser(ignore_unknown=True, mode = 'last'), 'SL')
    _test_parser_type(BUIDParser(ignore_unknown=False, mode = 'last'), 'DP')
    _test_parser_type(BUIDParser(ignore_unknown=True, mode = 'unique'), None)



# def test_parser_extended(bdb):
    
#     ent = bdb.get_entity('WB3001')
#     with pytest.deprecated_call():
#         ent.create_component_path('P1')

#     component_name ='T1'
#     folder = 'barely-db://Webs/WB3001_SL_LGA1'
#     folder_path = Path(bdb.resolve_file(folder))

#     contains_component,path_to_component = check_folder_contains_component(folder_path, component_name)
#     if contains_component:
#         shutil.rmtree(path_to_component, ignore_errors=True)

#     contains_component,path_to_component = check_folder_contains_component(folder_path, component_name)
#     assert(not contains_component)

#     ent.create_component_path(component_name)

#     contains_component,path_to_component = check_folder_contains_component(folder_path, component_name)
#     assert(contains_component)

#     os.rmdir(path_to_component)

#     contains_component,path_to_component = check_folder_contains_component(folder_path, component_name)
#     assert(not contains_component)



    
    
