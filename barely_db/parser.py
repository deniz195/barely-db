import logging
import collections
import typing
import attr
import cattr

import datetime
# import numpy as np
# import pandas as pd
import sys
import os
import copy

import json
# import yaml
import re
from pathlib import Path, PureWindowsPath

from collections import OrderedDict
from collections.abc import Sequence, Container

__all__ = ['BUIDParser']

# create logger
module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.DEBUG)

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
        'equipment': 'EQ',
        'manufacturing_orders': 'MO',
    }

    buid_regex = re.compile(r'([a-zA-Z]{2,3})(\d{2,5})')
    buid_comp_regex = re.compile(r'([a-zA-Z]{2,3})(\d{2,5})-?([a-zA-Z]{1,2}\d{1,5})?')
    buid_comp_must_regex = re.compile(r'([a-zA-Z]{2,3})(\d{2,5})-([a-zA-Z]{1,2}\d{1,5})')
    
    ignore_unknown = None

    def __init__(self, ignore_unknown=None, warn_empty=True, mode = 'unique', 
                       allow_components=True, allowed_types = None):
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

        if allowed_types is None:
            pass
        else:
            if ignore_unknown is False:
                raise ValueError('ignore_unknown cannot be set to False when allowed_types are specified!')
            elif ignore_unknown is None:
                ignore_unknown = True

            self.buid_types = {k: v for k, v in self.buid_types.items() if v in allowed_types}
            # module_logger.debug(f'Buid parsing restricted to types {self.buid_types.values()}')


        self.ignore_unknown = ignore_unknown
        self.warn_empty = warn_empty
        self.mode = mode
        self.allow_components = allow_components



    def __call__(self, buid_str):
        return self.parse(buid_str)

    def parse(self, buid_str):        
        regex = self.buid_comp_regex if self.allow_components else self.buid_regex
        regex_result = self.find(str(buid_str), regex)
        
        if regex_result is None:
            return None
        
        if self.mode in ['first', 'last', 'unique']:
            result = self.format_buid_from_regex(regex_result)
        else:
            result = [self.format_buid_from_regex(r) for r in regex_result]
            
        return result

    def parse_component(self, buid_str):        
        regex = self.buid_comp_must_regex
        regex_result = self.find(str(buid_str), regex)
        
        if regex_result is None:
            return None
        
        if self.mode in ['first', 'last', 'unique']:
            result = self.format_component_from_regex(regex_result)
        else:
            result = [self.format_component_from_regex(r) for r in regex_result]
            
        return result

    def parse_type(self, buid_str):        
        regex = self.buid_regex
        regex_result = self.find(str(buid_str), regex)
        
        if regex_result is None:
            return None
        
        if self.mode in ['first', 'last', 'unique']:
            result = self.format_type_from_regex(regex_result)
        else:
            result = [self.format_type_from_regex(r) for r in regex_result]
            
        return result

    def find(self, buid_str, regex):
   
        res = regex.findall(buid_str)
            
        if self.ignore_unknown:
            res = [r for r in res if self.is_known_buid_type(r)]
        
        if self.mode in ['all_unique', 'unique']:
            # res = list(set(res)) # remove duplicates
            
            # Remove duplicates but keep order:
            # https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-whilst-preserving-order
            def f7(seq):
                seen = set()
                seen_add = seen.add
                return [x for x in seq if not (x in seen or seen_add(x))]

            res = f7(res)


        if self.mode in ['last']:
            res.reverse()
    
#         res = [self.format_buid_from_regex(r) for r in res]

        if len(res) == 0:
            if self.mode in ['first', 'last', 'unique']:
                if self.warn_empty:
                    module_logger.warning(f'No valid buid found in {buid_str}')
                return None

        elif len(res) > 1:
            if self.mode in ['unique']:
                res_formated = [self.format_buid_from_regex(r) for r in res]
                module_logger.warning(f'More than one valid buid found in {buid_str} ({res_formated}!')
                return None

        if self.mode in ['first', 'last', 'unique']:
            return res[0]
        else:
            return res

    def is_known_buid_type(self, regex_result):
        buid_type = regex_result[0].upper()
        return buid_type in self.buid_types.values()

    def format_buid_from_regex(self, regex_result,):        
        buid_type = regex_result[0].upper()
        buid_id = int(regex_result[1])
        if len(regex_result) >= 3 and regex_result[2]:
            comp_id = f'-{regex_result[2]}'
        else:
            comp_id = ''
            
        if self.ignore_unknown is None:
            if not self.is_known_buid_type(regex_result):
                module_logger.warning(f'Unknown buid type {buid_type} in {repr(regex_result)}!')

        return '{}{:04d}{}'.format(buid_type, buid_id, comp_id)

    def format_component_from_regex(self, regex_result, ):        
        if len(regex_result) >= 3 and regex_result[2]:
            comp_id = f'{regex_result[2]}'
        else:
            comp_id = ''
            module_logger.warning(f'No buid component found when requested!')
            
        return f'{comp_id}'

    def format_type_from_regex(self, regex_result, ): 
        buid_type = regex_result[0].upper()       
        return f'{buid_type}'

    def attrib(self, *args, **kwds):
        ''' Creates an attr attribute that parses buids, based on the
        the given parser.'''
        kwds['converter'] = (lambda x: kwds['converter'](self(x))) if 'converter' in kwds else self
        kwds['validator'] = lambda obj, attr, value: self(value) is not None

        return attr.ib(**kwds)
