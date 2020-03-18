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

import objectpath # http://objectpath.org/reference.html

# from .file_management import FileManager, FileNameAnalyzer, serialize_to_file, open_in_explorer
from .parser import *
from .file_management import *
# from .tools import *

__all__ = ['BUIDParser', 'BarelyDB', 'BarelyDBEntity', 'FileManager', 'FileNameAnalyzer', 'serialize_to_file', 'open_in_explorer', 'ClassFileSerializer']

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

    # default_base_path = 'G:\\My Drive\\Battrion_AG\\DATABASE'
    # create list of possible default base paths 
    default_base_path = [\
        'G:\\Team Drives\\Database',
        'G:\\Shared drives\\Database',
        '/Volumes/GoogleDrive/Team Drives/Database',
        '/Volumes/GoogleDrive/Teamablagen/Database',
        '/Volumes/GoogleDrive/Geteilte Ablagen/Database',
        'G:\\Geteilte Ablagen\\Database',
        'G:\\Drive partagés\\Database',
        '/home/pi/GoogleDrive/database',
        '/home/jovyan/database',
        ]      

    known_bases = [\
        'G:\\My Drive\\Battrion_AG\\DATABASE\\',
        'G:\\Team Drives\\Database\\',
        'G:\\Shared drives\\Database\\',
        'G:\\Geteilte Ablagen\\Database\\',
        'G:\\Drive partagés\\Database\\',
        '/home/pi/GoogleDrive/database/',
        '/home/jovyan/database/',
        'barelydb://',
        'barely-db://',
        ]

    base_path = None
    property_file_glob = '*.property.json'
    preferred_property_files = []
    ignored_files = ['desktop.ini']

    buid_types = BUIDParser.buid_types
    buid_type_paths = None

    def __init__(self, base_path=None, path_depth=0, auto_reload_components = True):
        self.logger = module_logger

        self.path_depth = path_depth
        # if base path is None, check default base path for existance and
        # break at first existing path 
        if base_path is None:
            for def_base_path in self.default_base_path:
                if os.path.exists(def_base_path):
                    base_path = def_base_path
                    self.logger.info(f'Using default path {base_path}')
                    break

        if base_path is None:
            raise RuntimeError('Could not automatically determine base path of database!')

        self.base_path = Path(base_path)
        self.base_path = self.base_path.resolve().absolute()

        self.auto_reload_components = auto_reload_components

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


        self.known_bases_re = [re.compile(re.escape(b), re.IGNORECASE) for b in self.known_bases]


    def resolve_file(self, filename):
        base_path_str = f'{str(self.base_path)}{os.sep}'
        base_path_str = base_path_str.replace('\\', '\\\\')
        # check if path structure of filename is Windows-like 
        is_windows = False
        is_URL_like = False
        if "\\" in filename:
            is_windows = True
        elif "://" in filename:
            is_URL_like = True

        for b_re in self.known_bases_re:
            filename = b_re.sub(base_path_str, filename)
            # if file is windows like and have a unix like filing system 
            if is_windows and ('/' in base_path_str):
                filename = filename.replace("\\","/") # replace backslashes to forward slashes 
            # check it is the other way around        
            elif (not is_windows) and (not is_URL_like) and ('\\' in base_path_str):
                filename = filename.replace("/","\\")

        return filename

    def relative_file(self, filename):
        filename = Path(self.resolve_file(filename))
        file_rel = Path(filename).relative_to(self.base_path).as_posix()
        return str(file_rel)

    def absolute_file(self, file_rel):
        file_abs = str(self.base_path.joinpath(file_rel).resolve().absolute())

        # this is for safety to make sure that the path is really relative to base_path
        try:
            file_rel_recover = self.relative_file(file_abs)
            file_abs_recover = str(self.base_path.joinpath(file_rel_recover).resolve().absolute())
        except ValueError:
            raise ValueError(f'Given relative file name is not result in a file in the given database! ({file_rel})')

        return str(file_abs_recover)


    def get_code_paths(self, depth=1, add_to_sys_path=False, relative_bdb_path=True):              
        module_logger.warning('get_code_paths is is deprecated!')

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
                sys.path.insert(0, p)
                
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
        found_buid = [list(t) for t in zip(*candidates_buid)]
        found_buid = found_buid[0]
        duplicate_buid = [item for item, count in collections.Counter(found_buid).items() if count > 1]
        duplicate_buid = [i for i in duplicate_buid if i]
        if duplicate_buid:
            self.logger.warning(f'Following entities have multiple paths/folders: {duplicate_buid}')

        self.entity_paths = {buid: path for buid, path in candidates_buid if buid is not None}
        self.logger.info(f'Entities found: {len(self.entity_paths)}')

        # Scan all paths and determine target directories for each buid type!
        self.buid_type_paths = {}

        buid_types_done = set()
        buid_p = self.buid_scan

        for buid, entity_path in self.entity_paths.items():
            buid_type = buid_p.parse_type(buid)

            if buid_type in buid_types_done:
                pass
            else:
                if buid_type in self.buid_type_paths:
                    # if this type was already registered, check if parent path is the same
                    if self.buid_type_paths[buid_type] == entity_path.parent:
                        pass
                    else:
                        module_logger.warning(f'Entity {buid} has a base path that does not match with other entities of the same type ({buid_type})!')
                        buid_types_done.add(buid_type)
                else:
                    # if this is the first entity of this type use the parent directory
                    self.buid_type_paths[buid_type] = entity_path.parent

        for buid_type, buid_path in self.buid_type_paths.items():
            self.logger.info(f'{buid_type} --> {buid_path}')
                    




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
        
        # self.logger.debug(f'Components for {base_buid} found: {len(component_paths)}')
        
        
        
    @property
    def entities(self):
        return list(self.entity_paths.keys())

    # #### Deprecated. Replaced by get_entity_path
    # def entity_path(self, buid, absolute=False):
    #     self.logger.warning('entity_path is deprecated! use get_entity_path instead!')
    #     return self.get_entity_path(buid, absolute=absolute)

    def get_free_buid(self, start_buid, no_buids = 1, no_free_biuds=None):
        buid_p = BUIDParser()

        btype, bid = buid_p.parse_type_and_uid(start_buid)
        bid = int(bid)

        if no_free_biuds is None:
            no_free_biuds = no_buids
        
        found_buids = []

        while bid < 9999:
            new_buid = buid_p.format(btype, bid)
            bid += 1
            if new_buid in self.entities:
                found_buids = []
            else:
                found_buids += [new_buid]
                if len(found_buids) >= no_free_biuds:
                    break

        return found_buids[0:no_buids]
        

    def create_entity_path(self, buid, comment, absolute=False, reload=True):       
        buid = self.buid_normalizer(buid)
        buid_type = self.buid_normalizer.parse_type(buid)

        try:
            buid_path = self.get_entity_path(buid, absolute=absolute)
            return buid_path
        except KeyError:
            # entity does not exist
            pass

        # create new path
        buid_base_path = Path(self.buid_type_paths[buid_type])
        buid_path = buid_base_path.joinpath(f'{buid}_{comment}')

        # path = self.entity_paths[buid]
        if absolute:
            buid_path = buid_path.resolve().absolute()
        
        buid_path.mkdir(parents=False, exist_ok=True)

        if reload:
            self.load_entities()

        return buid_path


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
        if self.auto_reload_components or (buid not in self.component_paths):
            self.load_components(buid)
                       
        paths = self.component_paths[buid]
        if absolute:
            paths = {comp: Path(path).resolve().absolute() for comp, path in paths.items()}
        return paths

    def get_component_path(self, buid, component, absolute=False):
        component_paths = self.get_component_paths(buid, absolute=absolute)
        
        if component in component_paths:
            return component_paths[component]    
        else:
            raise FileNotFoundError(f'No path for component {component} in {buid}!')
    
    # #### Deprecated. Replaced by get_entity_path
    # def entity_files(self, buid, glob, must_contain_buid = False, output_as_str=True):
    #     self.logger.warning('entity_files is deprecated! use get_entity_files instead!')
    #     return self.get_entity_files(buid, glob, must_contain_buid=must_contain_buid, output_as_str=output_as_str)

    def _get_files(self, buid, path, glob, must_contain_buid = False, output_as_str=True):
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

    def get_component_files(self, buid, component, glob, must_contain_buid = False, output_as_str=True):
        buid = self.buid_normalizer(buid)        
        path = self.get_component_path(buid, component)
        return self._get_files(buid, path, glob, must_contain_buid=must_contain_buid, output_as_str=output_as_str)

    def get_entity_files(self, buid, glob, must_contain_buid = False, output_as_str=True):
        buid = self.buid_normalizer(buid)        
        path = self.get_entity_path(buid)
        return self._get_files(buid, path, glob, must_contain_buid=must_contain_buid, output_as_str=output_as_str)




    def entity_properties_files(self, buid, output_as_str=True):
        module_logger.warning('Property interface of BarelyDB is deprecated!')
        buid = self.buid_normalizer(buid)        
        files = self.get_entity_files(buid, self.property_file_glob, output_as_str=output_as_str)
        return list(files)

    def load_entity_properties(self, buid):
        module_logger.warning('Property interface of BarelyDB is deprecated!')
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
                        self.logger.warning(f'Property file has no buid specification {fn.name}!')
                        new_property_data['buid'] = BUID.INVALID

                    if 'source' not in new_property_data:
                        self.logger.warning(f'Property file has no source specification {fn.name}!')
                        new_property_data['source'] = 'Unknown source!'

                    properties[fn.name] = new_property_data
                    
            except:
                raise RuntimeError(f'Error in property file {str(fn)}')

        self.entity_properties[buid] = properties

    def reload_entity_properties(self, buid = None):
        module_logger.warning('Property interface of BarelyDB is deprecated!')
        buids = self.entity_properties.keys() if buid is None else [buid]
        
        for buid in buids:
            self.load_entity_properties(buid)           

    def get_entity_properties(self, buid, reload = False):
        module_logger.warning('Property interface of BarelyDB is deprecated!')
        buid = self.buid_normalizer(buid)       

        if (buid not in self.entity_properties) or reload:
            self.load_entity_properties(buid)

        return self.entity_properties[buid]

    def get_entity_tree(self, buid):
        module_logger.warning('Property interface of BarelyDB is deprecated!')
        buid = self.buid_normalizer(buid)       
        tree = objectpath.Tree(self.get_entity_properties(buid))
        return tree

    def add_preferred_file(self, prop_file):
        module_logger.warning('Property interface of BarelyDB is deprecated!')
        self.preferred_property_files = list(set(self.preferred_property_files + [prop_file]))

    def clear_preferred_files(self):
        module_logger.warning('Property interface of BarelyDB is deprecated!')
        self.preferred_property_files = []

    def query_property(self, buid, prop, property_file = '', source = '', warn_empty = True):
        module_logger.warning('Property interface of BarelyDB is deprecated!')
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
                self.logger.warning(f'No value for {prop} in entity {buid}!')
            return None
        elif len(result) == 1:
            return make_item(result[0])
        elif len(result) > 1:
            # try to remove ambiguity by self.preferred_property_files
            
            selector = [f'("{p}" in @.property_file)' for p in self.preferred_property_files]
            selector = ' or '.join(selector)
            selector = f'[{selector}]' if selector else ''
            # self.logger.warning(str(selector))

            tree = objectpath.Tree(result)
            result_amb = list(tree.execute(f'$..*{selector}'))            

            if len(result_amb) == 0:
                self.logger.warning(f'Multiple sources for {prop} in entity {buid}! Filtering with preferred files did not yield a result. Please, refine this query adding a property file to preferred_property_files! Found sources follow below:')
                for res in result:
                    self.logger.warning(json.dumps(res, indent=4))
                return None
            elif (len(result_amb) == 1):
                return make_item(result_amb[0])
            elif (len(result_amb) > 1):
                self.logger.warning(f'Multiple sources for {prop} in entity {buid}, even after filtering with preferred_property_files! Please, remove entries from preferred_property_files to lift this ambiguity! Found sources follow below:')
                for res in result_amb:
                    self.logger.warning(json.dumps(res, indent=4))
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
        module_logger.warning('Property interface of BarelyDB is deprecated!')
        buid = self.buid_normalizer(buid)       

        result = []
        for p in props:
            if type(p) == dict:
                result.append(self.query_property(buid, **p)) 
            else:
                result.append(self.query_property(buid, str(p))) 

        return result


    def get_entity(self, buid):
        return BarelyDBEntity(buid, self)





class BarelyDBEntity(object):
    file_manager = None
    
    @classmethod
    def like(cls, entity):
        ''' Copy constructor for subclasses '''
        return cls(buid=entity.buid_with_component, parent_bdb=entity.bdb)

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
    
    def __eq__(self,other):
        return self.buid_with_component == other.buid_with_component


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


    def create_entity_path(self, path_comment):
        entity_path = self.bdb.create_entity_path(self.buid, comment=path_comment)
        return entity_path

    def create_component_path(self, component, path_comment):
        if component is None:
            component = self.component

        if component is None:
            raise ValueError(f'Cannot create component path if no component is specified ({self.buid_with_component})!')
        
        existing_path = self.get_component_paths().get(component, None)
        if existing_path is not None:
            self.logger.warning(f'Component path already exists! {str(existing_path)}')
            return None
                
        base_bath = self.bdb.get_entity_path(self.buid)
        path_name = f'-{component}'
        if path_comment is not None:
            path_name += f'_{str(path_comment)}'

            
        component_path = base_bath.joinpath(path_name)
        component_path.mkdir(parents=False, exist_ok=True)            
        
        self.bdb.load_components(self.buid)
        
        return component_path
            
    def get_free_buid(self, no_buids = 1, no_free_biuds=None):
        return self.bdb.get_free_buid(self.buid_with_component, 
                                        no_buids=no_buids, 
                                        no_free_biuds=no_free_biuds)

        
    # ### Deprecated! Replaced by get_entity_path
    # def entity_path(self, absolute=False):
    #     return self.bdb.entity_path(self.buid, absolute=absolute)      

    def get_entity_path(self, absolute=False):
        return self.bdb.get_entity_path(self.buid, absolute=absolute)      

    def open_entity_path(self):
        if self.component is None:
            open_in_explorer(self.get_entity_path(absolute=True))
        else:
            open_in_explorer(self.get_component_path(absolute=True))

    def get_entity_name(self):
        return self.bdb.get_entity_name(self.buid)      

    # ### Deprecated! Replaced by get_entity_files
    # def entity_files(self, *args, **kwds):
    #     return self.bdb.entity_files(self.buid, *args, **kwds)

    def get_entity_files(self, glob, must_contain_buid = False, output_as_str=True):
        return self.bdb.get_entity_files(self.buid, glob, must_contain_buid=must_contain_buid, output_as_str=output_as_str)

    def get_component_files(self, glob, component=None, must_contain_buid = False, output_as_str=True):
        if component is None:
            component = self.component

        return self.bdb.get_component_files(self.buid, component, glob, must_contain_buid=must_contain_buid, output_as_str=output_as_str)

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
    

    def has_object(self, object_class, allow_parent=None):
        filename = object_class.file_serializer.resolve_file_from_entity(self, allow_parent=allow_parent)
        if filename is None:
            return False
        else:
            return Path(filename).exists()

    def load_object(self, object_class, default=None):
        try:
            obj = object_class.load_from_entity(self)
        except (FileNotFoundError, KeyError):
            self.logger.warning(f'No {object_class.__qualname__} object found for {self.buid_with_component}!')
            obj = None

        if obj is None and default is not None:
            self.logger.warning(f'Using default object!')
            obj = copy.copy(default)
            
        return obj


    def save_object(self, obj, **kwds):
        filename = obj.save_to_entity(self, **kwds)

        return filename
