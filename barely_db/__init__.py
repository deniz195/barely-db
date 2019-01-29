import logging

import typing
import attr
import cattr

import datetime
import numpy as np
import pandas as pd
import pint
import sys
import os

import json
import yaml
import re
from pathlib import Path

from collections import OrderedDict
from collections.abc import Sequence, Container

import objectpath # http://objectpath.org/reference.html

from .file_management import FileManager, FileNameAnalyzer

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
    }

    buid_regex = re.compile(r'([a-zA-Z]{2,3})(\d{2,5})')
    buid_comp_regex = re.compile(r'([a-zA-Z]{2,3})(\d{2,5})-?([a-zA-Z]{1,2}\d{1,5})?')
    buid_comp_must_regex = re.compile(r'([a-zA-Z]{2,3})(\d{2,5})-([a-zA-Z]{1,2}\d{1,5})')
    
    ignore_unknown = None

    def __init__(self, ignore_unknown=None, warn_empty=True, mode = 'unique', allow_components=True):
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

#     def parse_component(self, buid_str):
#         regex_result = self.find(str(buid_str), self.buid_comp_regex)
#         if self.allow_components:
#             res = self.buid_comp_regex.findall(buid_str)
#         else:
#             res = self.buid_regex.findall(buid_str)
        
#         return     

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

    def find(self, buid_str, regex):
    
        res = regex.findall(buid_str)
            
        if self.ignore_unknown == True:
            res = [r for r in res if self.is_known_buid_type(r)]
        
        if self.mode in ['all_unique', 'unique']:
            res = list(set(res)) # remove duplicates

        if self.mode in ['last']:
            res.reverse()
    
#         res = [self.format_buid_from_regex(r) for r in res]

        if len(res) == 0:
            if self.mode in ['first', 'last', 'unique']:
                if self.warn_empty:
                    module_logger.warn(f'No valid buid found in {buid_str}')
                return None

        elif len(res) > 1:
            if self.mode in ['unique']:
                res_formated = [self.format_buid_from_regex(r) for r in res]
                module_logger.warn(f'More than one valid buid found in {buid_str} ({res_formated}!')
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
            if buid_type not in self.buid_types.values():
                module_logger.warn(f'Unknown buid type {buid_type} in {repr(regex_result)}!')

        return '{}{:04d}{}'.format(buid_type, buid_id, comp_id)

    def format_component_from_regex(self, regex_result, ):        
        if len(regex_result) >= 3 and regex_result[2]:
            comp_id = f'{regex_result[2]}'
        else:
            comp_id = ''
            module_logger.warn(f'No buid component found when requested!')
            
        return f'{comp_id}'


    def attrib(self, *args, **kwds):
        ''' Creates an attr attribute that parses buids, based on the
        the given parser.'''
        kwds['converter'] = (lambda x: kwds['converter'](self(x))) if 'converter' in kwds else self
        kwds['validator'] = lambda obj, attr, value: self(value) is not None

        return attr.ib(**kwds)


# class BUID(object):
#     ''' Handles unique IDs of the form XXYYYY where XX is a two letter string 
#     and YYYY is a 4 letter number.
#     '''

#     INVALID = 'XX9999'

#     # instance variables and methods
#     def __init__(self, buid_str, do_normalize=True):
#         if do_normalize:
#             self.buid = BUIDParser()(buid_str)
#         else:
#             self.buid = buid_str

#     def __repr__(self):
#         return f'{self.__class__.__qualname__}(\'{self.buid}\')'

#     def __str__(self):
#         if self.buid is None:
#             return BUID.INVALID
#         else:
#             return self.buid



def test_BUID():
    buid_p = BUIDParser(ignore_unknown=True, mode = 'unique')

    aa = BUID(buid_p('XasfwX_sl293__Y'))
    print(repr(aa))
    print(str(aa))

    def _test_normalization(s):
        buid = buid_p.parse(s)
        print(f'{s} --> {buid}')

    print(f'Normal BUID parsing:')
    _test_normalization('XasfwX_sl293_sl293__Y')
    _test_normalization('XasfwX_sl293_sl333__Y')
    _test_normalization('lorem ipsum')
    _test_normalization('SL000293')
    _test_normalization('WB0251')
    _test_normalization('WB0252-D2')
    _test_normalization('WB0252-AFD2')
    _test_normalization('WB0252-AFD21231451')  
                  
    def _test_components(s):
        buid = buid_p.parse_component(s)
        print(f'{s} --> {buid}')
                  
    print(f'Only components:')
    _test_components('WB0252-D2')
    _test_components('CL0152-N50')
    _test_components('WB0252')

    buid_p2 = BUIDParser(ignore_unknown=True, mode = 'unique', allow_components = False)

    def _test_normalization(s):
        buid = buid_p2.parse(s)
        print(f'{s} --> {buid}')
                  
    print(f'No components:')
    _test_normalization('WB0252-D2')
    _test_normalization('WB0252')
              
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

# class SourcedItem(float):
#     name = None
#     value = None
#     property_file = None
#     source = None

#     @classmethod
#     def make(cls, name, value, property_file, source):       
#         new_item = cls(value)
#         new_item.name = name
#         new_item.property_file = property_file
#         new_item.source = source

#     def __init__(self, name, value, property_file, source):
#         self.name = name
#         self.value = value
#         self.property_file = property_file
#         self.source = source

#     def as_dict(self):
#         return {self.name: {'value': self.value, 'property_file': self.property_file, 'source': self.source}}

#     def __str__(self):
#         return f'{self.name} = {self.value} (from {self.property_file}, {self.source})'

#     def __repr__(self):
#         return "%s(**%s)" % (self.__class__.__qualname__, self.__dict__)


# class SourcedItem(float):
#     name = None
#     value = None
#     property_file = None
#     source = None

#     @classmethod
#     def make(cls, name, value, property_file, source):       
#         new_item = cls(value)
#         new_item.name = name
#         new_item.property_file = property_file
#         new_item.source = source
#         return new_item

#     def as_dict(self):
#         return {self.name: {'value': self.value, 'property_file': self.property_file, 'source': self.source}}

#     def __str__(self):
#         return f'{self.name} = {self.value} (from {self.property_file}, {self.source})'

#     def __repr__(self):
#         return "%s(**%s)" % (self.__class__.__qualname__, self.__dict__)


from collections import namedtuple
SourcedItem = namedtuple('SourcedItem', 'name, value, property_file, source')


class BarelyDB(object):

    base_path = None
    property_file_glob = '*.property.json'
    preferred_property_files = []
    ignored_files = ['desktop.ini']

    def __init__(self, base_path, path_depth=0):
        self.path_depth = path_depth
        self.base_path = Path(base_path)
        self.base_path = self.base_path.resolve().absolute()

        self.logger = module_logger

        self.entity_paths = {}
        self.entity_properties = {}
        self.component_paths = {}

        self.buid_normalizer = BUIDParser(ignore_unknown=True, 
                                          mode = 'unique', 
                                          warn_empty = True,
                                          allow_components=False
                                         )
        
        self.buid_scan = BUIDParser(ignore_unknown=True, 
                                    mode = 'first', 
                                    warn_empty = False, 
                                    allow_components=False)        

        
    def get_code_paths(self, depth=1, add_to_sys_path=False, relative_bdb_path=True):              
        
        code_path_valid = False
    
        if relative_bdb_path:
            code_path = ''
            for p in Path(__file__).absolute().parts:
                code_path = Path(code_path).joinpath(p)
                if p.find('__code') >= 0:
                    code_path_valid = True
                    break
            
            if not code_path_valid:
                self.logger.warning(f'No code path found, relative to bdb code path {code_path}! Using default code in base_path!')
                
                    

        if not code_path_valid:
            code_path = self.base_path.joinpath('__code')

        # sys.path.append(str(bdb_code_path))
        paths = [code_path]
        for p in code_path.iterdir():
            if p.is_dir(): 
                paths.append(p)
             
        paths = [str(p) for p in paths]
        if add_to_sys_path:
            for p in paths:
                sys.path.append(p)
                
        return paths
        

    def load_entities(self):
        # candidates = [x.relative_to(self.base_path) for x in self.base_path.iterdir() if x.is_dir()]
        def iter_subdir(path, depth=0):
            for sub in path.iterdir():
                if sub.is_dir():
                    if depth == 0:    
                        yield sub
                    else:
                        for sub in iter_subdir(sub, depth-1):
                            yield sub
       
        
        # candidates = [x for x in self.base_path.iterdir() if x.is_dir()]
        
        candidates = iter_subdir(self.base_path, depth=self.path_depth)

        buid_p = self.buid_scan
            
        candidates_buid = [(buid_p(c), c) for c in candidates]
        self.entity_paths = {buid: path for buid, path in candidates_buid if buid is not None}
        self.logger.info(f'Entities found: {len(self.entity_paths)}')
        

    def load_components(self, buid, absolute=False):
        entity_path = self.get_entity_path(buid, absolute=absolute)
        base_buid = self.buid_normalizer(buid)       

        def iter_subdir(path, depth=0):
            for sub in path.iterdir():
                if sub.is_dir():
                    if depth == 0:    
                        yield sub
                    else:
                        for sub in iter_subdir(sub, depth-1):
                            yield sub
       
        
        candidates = iter_subdir(entity_path, depth=0)

        def component_parser(component_path):
            return self.buid_scan.parse_component(base_buid + component_path.name)
            
        candidates_components = [(component_parser(c), c) for c in candidates]
        component_paths = {component: path \
             for component, path in candidates_components \
             if component is not None}
        
        self.component_paths[base_buid] = component_paths
        
        self.logger.info(f'Components for {base_buid} found: {len(component_paths)}')
        
        
        
    @property
    def entities(self):
        return list(self.entity_paths.keys())

    #### Deprecated. Replaced by get_entity_path
    def entity_path(self, buid, absolute=False):
        self.logger.warn('entity_path is deprecated! use get_entity_path instead!')
        return self.get_entity_path(buid, absolute=absolute)

    def get_entity_path(self, buid, absolute=False):
        buid = self.buid_normalizer(buid)
        path = self.entity_paths[buid]
        if absolute:
            path = path.resolve().absolute()
        return path
    
    def get_entity_name(self, buid):
        path = self.get_entity_path(buid, absolute=True)
        return Path(path).parts[-1]

    def get_component_paths(self, buid, absolute=False):
        buid = self.buid_normalizer(buid)
        if buid not in self.component_paths:
            self.load_components(buid)
                       
        paths = self.component_paths[buid]
        if absolute:
            paths = [path.resolve().absolute() for path in paths]
        return paths

    def get_component_path(self, buid, component, absolute=False):
        component_paths = self.get_component_paths(buid, absolute=absolute)
        
        if component in component_paths:
            return component_paths[component]    
        else:
            raise FileNotFoundError(f'No path for component {component} in {buid}!')
    
    #### Deprecated. Replaced by get_entity_path
    def entity_files(self, buid, glob, must_contain_buid = False, output_as_str=True):
        self.logger.warn('entity_files is deprecated! use get_entity_files instead!')
        return self.get_entity_files(buid, glob, must_contain_buid=must_contain_buid, output_as_str=output_as_str)

        
    def get_entity_files(self, buid, glob, must_contain_buid = False, output_as_str=True):
        buid = self.buid_normalizer(buid)        
        path = self.get_entity_path(buid)
        files = path.glob(glob)

        def ignore_file(fn):
            return fn in self.ignored_files
        
        if must_contain_buid:
            buid_p = BUIDParser(ignore_unknown=False, mode = 'first', warn_empty = False)
            files_sel = [fn for fn in files if (buid_p(fn) == buid)]
            files = files_sel

        files = [fn for fn in files if not ignore_file(fn.name)]
                    
        if output_as_str:
            files = [str(fn) for fn in files]

        return list(files)


    def entity_properties_files(self, buid, output_as_str=True):
        buid = self.buid_normalizer(buid)        
        files = self.get_entity_files(buid, self.property_file_glob, output_as_str=output_as_str)
        return list(files)


    def load_entity_properties(self, buid):
        buid = self.buid_normalizer(buid)       
        old_properties = self.entity_properties.get(buid, {})

        files = self.entity_properties_files(buid, output_as_str=False)
                
        properties = {}
        properties['entity_path'] = self.get_entity_path(buid)
        
        self.load_components(buid)
        properties['component_paths'] = self.get_component_paths(buid)
        properties['components'] = list(self.get_component_paths(buid).keys())

        # self.component_paths[base_buid] = component_paths
        
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

    def get_entity_properties(self, buid, reload = False):
        buid = self.buid_normalizer(buid)       

        if (buid not in self.entity_properties) or reload:
            self.load_entity_properties(buid)

        return self.entity_properties[buid]

    def get_entity_tree(self, buid):
        buid = self.buid_normalizer(buid)       
        tree = objectpath.Tree(self.get_entity_properties(buid))
        return tree

    def add_preferred_file(self, prop_file):
        self.preferred_property_files = list(set(self.preferred_property_files + [prop_file]))

    def clear_preferred_files(self):
        self.preferred_property_files = []

    def query_property(self, buid, prop, property_file = '', source = '', warn_empty = True):
        buid = self.buid_normalizer(buid)       

        prop = str(prop)
        property_file = str(property_file)
        source = str(source)

        tree = self.get_entity_tree(buid)

        # query =  f'$..*[("{property_file}" in @.property_file)]'

        # query property together with file and source information
        selector = f'({prop} in @)'
        selector += f'and ("{property_file}" in @.property_file)'
        selector += f'and ("{source}" in @.source)'
        selector = f'[{selector}]'

        query =  f'$..*{selector}'
        query += f'.({prop}, property_file, source)'
        result = list(tree.execute(query))

        def make_item(res):
            return SourcedItem(name=prop, 
                        value=res[prop], 
                        property_file=res['property_file'], 
                        source=res['source'])

        if len(result) == 0:
            if warn_empty:
                self.logger.warn(f'No value for {prop} in entity {buid}!')
            return None
        elif len(result) == 1:
            return make_item(result[0])
        elif len(result) > 1:
            # try to remove ambiguity by self.preferred_property_files
            
            selector = [f'("{p}" in @.property_file)' for p in self.preferred_property_files]
            selector = ' or '.join(selector)
            selector = f'[{selector}]' if selector else ''
            # self.logger.warn(str(selector))

            tree = objectpath.Tree(result)
            result_amb = list(tree.execute(f'$..*{selector}'))            

            if len(result_amb) == 0:
                self.logger.warn(f'Multiple sources for {prop} in entity {buid}! Filtering with preferred files did not yield a result. Please, refine this query adding a property file to preferred_property_files! Found sources follow below:')
                for res in result:
                    self.logger.warn(json.dumps(res, indent=4))
                return None
            elif (len(result_amb) == 1):
                return make_item(result_amb[0])
            elif (len(result_amb) > 1):
                self.logger.warn(f'Multiple sources for {prop} in entity {buid}, even after filtering with preferred_property_files! Please, remove entries from preferred_property_files to lift this ambiguity! Found sources follow below:')
                for res in result_amb:
                    self.logger.warn(json.dumps(res, indent=4))
                return None
        
        # shouldnt arrive here
        return None

        # list(tree.execute("$..*[tsc in @].property_file"))

        # query = f'$..*[("{str(property_file)}" in @.property_file)].{str(prop)}'
        # result = list(tree.execute(query)


    def query_properties(self, buid, props):
        ''' Queries a list of properties. 

        Parameters: 
        props is a list of strings or dictionaries or mixed. 
        Strings are interpreted as the prop parameter to query_properties.
        Dictionaries as keyword parameters to query_properties.
        '''
        buid = self.buid_normalizer(buid)       

        result = []
        for p in props:
            if type(p) == dict:
                result.append(self.query_property(buid, **p)) 
            else:
                result.append(self.query_property(buid, str(p))) 

        return result






class BarelyDBEntity(object):
    file_manager = None
    
    def __init__(self, buid, parent_bdb):       
        self.logger = module_logger
        
        buid_p = BUIDParser(ignore_unknown=False, 
                    mode = 'first', 
                    warn_empty = True, 
                    allow_components=False)            
        self._buid = buid_p(buid)
        self._bdb = parent_bdb

        buid_comp_p = BUIDParser(ignore_unknown=False, 
                    mode = 'first', 
                    warn_empty = False, 
                    allow_components=False)                

        self.component = buid_comp_p.parse_component(buid)
        

    def __repr__(self):
        if self.component is None:
            return f'{self.__class__.__qualname__}(\'{self.buid}\')'
        else:
            return f'{self.__class__.__qualname__}(\'{self.buid}-{self.component}\')'
    
    @property
    def buid(self):
        return self._buid

    @property
    def buid_with_component(self):
        return self._buid + (f'-{self.component}' if self.component is not None else '')
    
    @property
    def bdb(self):
        return self._bdb

    def get_parent_entity(self):
        return BarelyDBEntity(self.buid, self.bdb)

    def resolve_relative_path(self, path, component = None):
        if component is None:
            component = self.component
            
        if component is None:
            base_bath = self.get_entity_path()
        else:
            base_bath = self.get_component_path(component)
            
        current_dir = str(Path.cwd())        
        os.chdir(str(base_bath))
        if type(path) in set([type(''), type(Path('.'))]):
            path_resolved = str(Path(path).resolve().absolute())
        elif isinstance(path, Sequence):
            path_resolved = [str(Path(p).resolve().absolute()) for p in path] 
        else:
            raise TypeError('path needs to be str, Path, or Sequence (list etc.)!')
        os.chdir(current_dir)
        
        return path_resolved
            
    def make_file_manager(self, 
                 component = None,
                 raw_path = './', 
                 export_path = './',  
                 export_prefix = '',
                 secondary_data_paths = [],
                 auto_string = True, 
                 auto_remove_duplicates = True,
                 **kwds):
        
        if component is None:
            component = self.component
            
        rebase_path = lambda p: self.resolve_relative_path(p, component)
                
        raw_path = rebase_path(raw_path)
        export_path = rebase_path(export_path)
        secondary_data_paths = [rebase_path(p) for p in secondary_data_paths]
        
        options = kwds.copy()
        options.update(dict(raw_path = raw_path, 
                            export_path = export_path,  
                            export_prefix = export_prefix,
                            secondary_data_paths = secondary_data_paths,
                            auto_string = auto_string, 
                            auto_remove_duplicates = auto_remove_duplicates,
                           ))
        
        return FileManager(**options)
                 
    def create_property_file(self,
                             operator,
                             source,
                             property_file,
                             **properties
                            ):
                
        output = OrderedDict(buid = self.buid,
                             operator = operator,
                             source = source,
                            )
        
        output.update(properties)
        
        json_default_opts = dict(indent=4)
        output_json = json.dumps(output, **json_default_opts)
        
        property_file_res = self.resolve_relative_path(property_file)
        with open(property_file_res, 'w') as fp:
            fp.write(output_json)  
        self.logger.info(f'Property written to file {property_file}.')
        
    def create_component_path(self, component, path_comment=None):
        if component is None:
            component = self.component
        
        existing_path = self.get_component_paths().get(component, None)
        if existing_path is not None:
            self.logger.warn(f'Component path already exists! {str(existing_path)}')
            return None
                
        base_bath = self.bdb.get_entity_path(self.buid)
        path_name = f'-{component}'
        if path_comment is not None:
            path_name += f'_{str(path_comment)}'

            
        component_path = base_bath.joinpath(path_name)
        component_path.mkdir(parents=False, exist_ok=True)            
        
        self.bdb.load_components(self.buid)
        
        return component_path
            
        
        
    ### Deprecated! Replaced by get_entity_path
    def entity_path(self, absolute=False):
        return self.bdb.entity_path(self.buid, absolute=absolute)      

    def get_entity_path(self, absolute=False):
        return self.bdb.get_entity_path(self.buid, absolute=absolute)      

    def get_entity_name(self):
        return self.bdb.get_entity_name(self.buid)      

    ### Deprecated! Replaced by get_entity_files
    def entity_files(self, *args, **kwds):
        return self.bdb.entity_files(self.buid, *args, **kwds)

    def get_entity_files(self, *args, **kwds):
        return self.bdb.get_entity_files(self.buid, *args, **kwds)

    def get_component_paths(self, absolute=False):
        return self.bdb.get_component_paths(self.buid, absolute=absolute)      
        
    def get_component_path(self, component=None, absolute=False):
        if component is None:
            component = self.component

        return self.bdb.get_component_path(self.buid, component, absolute=absolute)

    def component_files(self, glob, must_contain_buid = False, output_as_str=True, component=None):
        if component is None:
            component = self.component
        
        buid = self.buid_normalizer(buid)        
        path = self.get_entity_path(buid)
        files = path.glob(glob)

        def ignore_file(fn):
            return fn in self.ignored_files
        
        if must_contain_buid:
            buid_p = BUIDParser(ignore_unknown=False, mode = 'first', warn_empty = False)
            files_sel = [fn for fn in files if (buid_p(fn) == buid)]
            files = files_sel

        files = [fn for fn in files if not ignore_file(fn.name)]
                    
        if output_as_str:
            files = [str(fn) for fn in files]

        return list(files)
    
    
    
    def reload_entity_properties(self):
        return self.bdb.reload_entity_properties(self.buid)

    def get_entity_properties(self, reload = False):
        return self.bdb.get_entity_properties(self.buid, reload=reload)

    def get_entity_tree(self):
        return self.bdb.get_entity_tree(self.buid)

    def query_property(self, *args, **kwds):
        return self.bdb.query_property(self.buid, *args, **kwds)

    def query_properties(self, *args, **kwds):
        return self.bdb.query_properties(self.buid, *args, **kwds)
    

    
    
