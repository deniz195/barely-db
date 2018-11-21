import logging

import datetime
import numpy as np
import pandas as pd
import pint

import json
import re
from pathlib import Path

import objectpath # http://objectpath.org/reference.html

# create logger
module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.DEBUG)


from .db import *

# general useful module components
def _reload_module():
    import sys
    import importlib
    current_module = sys.modules[__name__]
    module_logger.info('Reloading module %s' % __name__)
    importlib.reload(current_module)


class BUIDParser(object):
    # class variables
    buid_types = {\
        'slurry': 'SL',
        'web': 'WB',
        'cells': 'CL',
        'electrochemistry': 'EE',
        'rawmaterial': 'RM',
        'experiment': 'EXP',
    }

    buid_regex = re.compile(r'([a-zA-Z]{2,3})(\d{2,5})')

    ignore_unknown = None

    def __init__(self, ignore_unknown=None, warn_empty=True, mode = 'unique'):
        ''' Creates a BUID parser. 
        Parameters:
        ignore_unknown = None: Parses unknown BUID types but warns
        ignore_unknown = True: Rejects unknown BUID types quietly
        ignore_unknown = False: Accepts unknown BUID types quietly

        warn_empty = True: Warns if no BUID was found!

        mode = 'unique': Default. Returns a single BUID if successfull, warns otherwise
        mode = 'first': Returns first BUID found
        mode = 'last': Returns last BUID found
        mode = 'all': Returns all BUIDs
        mode = 'all_unique': Returns all BUIDs, without duplicates
        '''

        self.ignore_unknown = ignore_unknown
        self.warn_empty = warn_empty
        self.mode = mode

    def __call__(self, buid_str):
        return self.parse(buid_str)

    def parse(self, buid_str):
        return self.find(str(buid_str))

    def find(self, buid_str):
        res = self.buid_regex.findall(buid_str)

        if self.ignore_unknown == True:
            res = [r for r in res if self.is_known_buid_type(r)]
        
        if self.mode in ['all_unique', 'unique']:
            res = list(set(res)) # remove duplicates

        if self.mode in ['last']:
            res.reverse()
    
        res = [self.format_buid_from_regex(r) for r in res]

        if len(res) == 0:
            if self.mode in ['first', 'last', 'unique']:
                if self.warn_empty:
                    module_logger.warn(f'No valid buid found in {buid_str}')
                return None

        elif len(res) > 1:
            if self.mode in ['unique']:
                module_logger.warn(f'More than one valid buid found in {buid_str} ({repr(res)}!')
                return None

        if self.mode in ['first', 'last', 'unique']:
            return res[0]
        else:
            return res


    def is_known_buid_type(self, regex_result):
        buid_type = regex_result[0].upper()
        return buid_type in self.buid_types.values()

    def format_buid_from_regex(self, regex_result):        
        buid_type = regex_result[0].upper()
        buid_id = int(regex_result[1])

        if self.ignore_unknown is None:
            if buid_type not in self.buid_types.values():
                module_logger.warn(f'Unknown buid type {buid_type} in {repr(regex_result)}!')

        return '{}{:04d}'.format(buid_type, buid_id)




class BUID(object):
    ''' Handles unique IDs of the form XXYYYY where XX is a two letter string 
    and YYYY is a 4 letter number.
    '''

    INVALID = 'XX9999'

    # instance variables and methods
    def __init__(self, buid_str, do_normalize=True):
        if do_normalize:
            self.buid = BUIDParser()(buid_str)
        else:
            self.buid = buid_str

    def __repr__(self):
        return f'{self.__class__.__qualname__}(\'{self.buid}\')'

    def __str__(self):
        if self.buid is None:
            return BUID.INVALID
        else:
            return self.buid



def test_BUID():
    buid_p = BUIDParser(ignore_unknown=True, mode = 'unique')

    aa = BUID(buid_p('XasfwX_sl293__Y'))
    print(repr(aa))
    print(str(aa))

    def _test_normalization(s):
        buid = buid_p.parse(s)
        print(f'{s} --> {buid}')

    _test_normalization('XasfwX_sl293_sl293__Y')
    _test_normalization('XasfwX_sl293_sl333__Y')
    _test_normalization('lorem ipsum')
    _test_normalization('SL000293')

    def _test_parser_mode(buid_p):
        s = 'XasfwX_sl293_sl333_dp241_sl333_dp241_Y'
        buid = buid_p(s)
        print(f'{s} --> {buid}')

    _test_parser_mode(BUIDParser(ignore_unknown=True, mode = 'all'))
    _test_parser_mode(BUIDParser(ignore_unknown=False, mode = 'all'))
    _test_parser_mode(BUIDParser(ignore_unknown=True, mode = 'all_unique'))
    _test_parser_mode(BUIDParser(ignore_unknown=False, mode = 'all_unique'))
    _test_parser_mode(BUIDParser(ignore_unknown=True, mode = 'first'))
    _test_parser_mode(BUIDParser(ignore_unknown=True, mode = 'last'))
    _test_parser_mode(BUIDParser(ignore_unknown=False, mode = 'last'))
    _test_parser_mode(BUIDParser(ignore_unknown=True, mode = 'unique'))


# BUID.buid_regex = re.compile(BUID.buid_regex_str)

class BarelyDB(object):

    base_path = None
    property_file_glob = '*.property.json'


    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.base_path = self.base_path.resolve().absolute()

        self.logger = module_logger

        self.entity_paths = {}
        self.entity_properties = {}

        self.buid_normalizer = BUIDParser(ignore_unknown=True, mode = 'unique', warn_empty = True)


    def load_entities(self):
        # candidates = [x.relative_to(self.base_path) for x in self.base_path.iterdir() if x.is_dir()]
        candidates = [x for x in self.base_path.iterdir() if x.is_dir()]

        buid_p = BUIDParser(ignore_unknown=True, mode = 'first', warn_empty = False)
        candidates_buid = [(buid_p(c), c) for c in candidates]
        self.entity_paths = {buid: path for buid, path in candidates_buid if buid is not None}
        self.logger.info(f'Entities found: {len(self.entity_paths)}')
        

    @property
    def entities(self):
        return list(self.entity_paths.keys())

    def entity_path(self, buid, absolute=False):
        buid = self.buid_normalizer(buid)
        path = self.entity_paths[buid]
        if absolute:
            path = path.resolve().absolute()
        return path

    def entity_files(self, buid, glob):
        buid = self.buid_normalizer(buid)        
        path = self.entity_path(buid)
        files = path.glob(glob)
        return list(files)


    def entity_properties_files(self, buid):
        buid = self.buid_normalizer(buid)        
        files = self.entity_files(buid, self.property_file_glob)
        return list(files)


    def load_entity_properties(self, buid):
        buid = self.buid_normalizer(buid)       
        old_properties = self.entity_properties.get(buid, {})

        files = self.entity_properties_files(buid)

        properties = {}
        for fn in files:
            try:
                with open(str(fn), 'r') as f:
                    new_property_data = json.load(f)
                    new_property_data['property_file'] = fn.name

                    if 'buid' not in new_property_data:
                        self.logger.warn(f'Property file has no buid specification {fn.name}!')
                        new_property_data['buid'] = BUID.INVALID

                    if 'source' not in new_property_data:
                        self.logger.warn(f'Property file has no source specification {fn.name}!')
                        new_property_data['source'] = 'Unknown source!'

                    properties[fn.name] = new_property_data
                    
            except:
                raise RuntimeError(f'Error in property file {str(fn)}')

        self.entity_properties[buid] = properties

    def reload_entity_properties(self, buid = None):
        buids = self.entity_properties.keys() if buid is None else [buid]
        
        for buid in buids:
            self.load_entity_properties(buid)           

    
    def get_entity_properties(self, buid):
        buid = self.buid_normalizer(buid)       

        if buid not in self.entity_properties:
            self.load_entity_properties(buid)

        return self.entity_properties[buid]


    # def query_property(self, buid, prop_name, property_file = '', source = ''):
    #     buid = self.buid_normalizer(buid)       
    #     tree = objectpath.Tree(self.get_entity_properties(buid))

    #     prop_name = str(prop_name)
    #     property_file = str(property_file)
    #     source = str(source)

    #     # query =  f'$..*[("{property_file}" in @.property_file)]'
    #     query =  f'$..*[("{prop_name}" in @)]'
    #     query += f'.({prop_name}, property_file, source)'
        
    #     result = list(tree.execute(query)

        # list(tree.execute("$..*[tsc in @].property_file"))

        # query = f'$..*[("{str(property_file)}" in @.property_file)].{str(prop_name)}'
        # result = list(tree.execute(query)







