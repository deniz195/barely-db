import logging
import collections
import typing
import attr
import cattr

import datetime
import sys
import os
import copy

import json
import re
from pathlib import Path, PureWindowsPath

from collections import OrderedDict
from collections.abc import Sequence, Container

# from .file_management import FileManager, FileNameAnalyzer, serialize_to_file, open_in_explorer
from .configs import *
from .parser import *
from .file_management import *

use_legacy = True
if use_legacy:
    from .legacy import BarelyDBLegacyInterfaceMixin, BarelyDBEntityLegacyInterfaceMixin
else:
    BarelyDBLegacyInterfaceMixin = object
    BarelyDBEntityLegacyInterfaceMixin = object

# from .tools import *
# Naming conventions: https://swift.org/documentation/api-design-guidelines/#strive-for-fluent-usage

__all__ = ['BarelyDB', 'BarelyDBConfig', 'BarelyDBSystemConfig', 'BarelyDBEntity', 'FileManager', 'FileNameAnalyzer', 'serialize_to_file', 'open_in_explorer', 'ClassFileSerializer', 'cattr_json_serialize']

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




class BarelyDB(BarelyDBLegacyInterfaceMixin):
    config = None
    base_path = None

    auto_reload_components = None

    buid_type_paths = {}

    path_converter = Path

    _MyBUIDParser = None

    def __init__(self, name=None, base_path=None, path_depth=None, auto_reload_components = True, path_converter = Path):
        self.logger = module_logger

        self.path_converter = path_converter

        # if base path is None, check default base path for existance and
        # break at first existing path 
        if base_path is None:
            sys_config = BarelyDBSystemConfig.load(default_to_empty=True)
            default_base_path = sys_config.default_base_path.get(name, [])

            for def_base_path in default_base_path:
                if os.path.exists(def_base_path):
                    base_path = def_base_path
                    self.logger.info(f'Using default path {base_path}')
                    break

        if base_path is None:
            raise RuntimeError('Could not automatically determine base path of database!')

        self.config = BarelyDBConfig.load(base_path)


        if path_depth:
            self.logger.warning('Deprecated: path_depth in constructor is deprecated!')

        self.auto_reload_components = auto_reload_components

        self.base_path = Path(base_path)
        self.base_path = self.base_path.absolute().resolve()

        self.entity_paths = {}
        self.entity_properties = {}
        self.component_paths = {}

        self._MyBUIDParser = GenericBUIDParser.create_class(self.config.buid_types)

        self.buid_normalizer = self.BUIDParser(ignore_unknown=True, 
                                          mode = 'unique', 
                                          warn_empty = True,
                                          allow_components=False
                                         )
        
        self.buid_scan = self.BUIDParser(ignore_unknown=True, 
                                    mode = 'first', 
                                    warn_empty = False, 
                                    allow_components=False)        


        self.known_bases_re = [re.compile(re.escape(b), re.IGNORECASE) for b in self.known_bases]


    @property
    def name(self):
        return self.config.name
    
    @property
    def path_depth(self):
        return self.config.path_depth
    
    @property
    def ignored_files(self):
        return self.config.ignored_files
    
    @property
    def known_bases(self):
        return self.config.known_bases
    
    @property
    def buid_types(self):
        return self.config.buid_types

    @property
    def BUIDParser(self):
        return self._MyBUIDParser

    def __repr__(self):
        return f'{self.__class__.__qualname__}(name={self.name} @ {self.base_path} + {self.path_depth})'

    def __getitem__(self, buid):
        return self.get_entity(buid)

    def get_entity(self, buid):
        return BarelyDBEntity(buid, self)

    @property
    def entities(self):
        return list(self.entity_paths.keys())




    def resolved_file(self, filename):
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
        filename = Path(self.resolved_file(filename))
        file_rel = Path(filename).relative_to(self.base_path).as_posix()
        return str(file_rel)

    def absolute_file(self, file_rel):
        file_abs = str(self.base_path.joinpath(file_rel).absolute().resolve())

        # this is for safety to make sure that the path is really relative to base_path
        try:
            file_rel_recover = self.relative_file(file_abs)
            file_abs_recover = str(self.base_path.joinpath(file_rel_recover).absolute().resolve())
        except ValueError:
            raise ValueError(f'Given relative file name is not result in a file in the given database! ({file_rel})')

        return str(file_abs_recover)

    @staticmethod
    def iter_subdir(path, depth=0):

        def _iter_subdir(path, depth=0):
            for sub in path.iterdir():
                if sub.is_dir():
                    if depth == 0:    
                        yield sub
                    else:
                        for sub in _iter_subdir(sub, depth-1):
                            yield sub

        return _iter_subdir(path, depth=depth)


    def load_entities(self, verbose=True):
        # candidates = [x.relative_to(self.base_path) for x in self.base_path.iterdir() if x.is_dir()]

        # candidates = [x for x in self.base_path.iterdir() if x.is_dir()]
        candidates = self.iter_subdir(self.base_path, depth=self.path_depth)
        buid_p = self.buid_scan
            
        candidates_buid = [(buid_p(c), c) for c in candidates]
        found_buids = [buid for buid, path in candidates_buid if buid is not None]
        self._duplicate_buid_count = collections.Counter(found_buids)
        self._duplicate_buid = [item for item, count in self._duplicate_buid_count.items() if item and count > 1]

        self.entity_paths = {buid: path for buid, path in candidates_buid if buid is not None}
        self.logger.info(f'Entities found: {len(self.entity_paths)}')

        self.check_for_duplicates(verbose=verbose)
        self.refresh_buid_type_paths(verbose=verbose)


    def check_for_duplicates(self, verbose=True):
        # Check for duplicates
        # found_buid = self.entity_paths.keys()
        duplicate_buid = self._duplicate_buid
        
        if duplicate_buid:
            self.logger.error(f'Following entities have multiple paths/folders: {duplicate_buid}')

        return bool(duplicate_buid)


    def refresh_buid_type_paths(self, verbose=True):
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

        if verbose:
            for buid_type, buid_path in self.buid_type_paths.items():
                self.logger.info(f'{buid_type} --> {buid_path}')


    def load_components(self, buid):
        entity_path = self.get_entity_path(buid)
        base_buid = self.buid_normalizer(buid)       

        candidates = self.iter_subdir(entity_path, depth=0)

        def component_parser(component_path):
            return self.buid_scan.parse_component(base_buid + component_path.name)
            
        candidates_components = [(component_parser(c), c) for c in candidates]
        component_paths = {component: path \
             for component, path in candidates_components \
             if component is not None}
        
        self.component_paths[base_buid] = component_paths
        
        # self.logger.debug(f'Components for {base_buid} found: {len(component_paths)}')
                
    def get_entity_path(self, buid):
        buid = self.buid_normalizer(buid)
        path = self.entity_paths[buid]
        path = path.absolute().resolve()
        return path
    
    def get_entity_name(self, buid):
        path = self.get_entity_path(buid)
        name_raw = Path(path).parts[-1]
        name_raw = name_raw.replace(buid, '')
        if name_raw[0] in [' ', '_']:
            name_raw = name_raw[1:]

        return name_raw

    def get_component_paths(self, buid):
        buid = self.buid_normalizer(buid)
        if self.auto_reload_components or (buid not in self.component_paths):
            self.load_components(buid)
                       
        paths = self.component_paths[buid]
        paths = {comp: Path(path).absolute().resolve() for comp, path in paths.items()}
        return paths

    def get_component_path(self, buid, component):
        component_paths = self.get_component_paths(buid)
        
        if component in component_paths:
            return component_paths[component]    
        else:
            raise FileNotFoundError(f'No path for component {component} in {buid}!')



    def create_new_entity(self, *, after, name, reload=True):
        new_buid = self._get_free_buid(after)[0]
        self._create_entity_path(new_buid, name, reload=reload)

        return self[new_buid]


    def _get_free_buid(self, after, no_buids = 1, no_free_biuds=None):
        buid_p = self.BUIDParser()

        btype, bid = buid_p.parse_type_and_uid(after)
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
        

    def _create_entity_path(self, buid, name, reload=True):       
        buid = self.buid_normalizer(buid)
        buid_type = self.buid_normalizer.parse_type(buid)

        try:
            buid_path = self.get_entity_path(buid)
            return buid_path
        except KeyError:
            # entity does not exist
            pass

        if buid_type not in self.buid_type_paths:
            raise ValueError(f'Do not know where to put entities of type {buid_type}!')

        # create new path
        buid_base_path = Path(self.buid_type_paths[buid_type])
        buid_path = buid_base_path.joinpath(f'{buid}_{name}')

        buid_path = buid_path.absolute().resolve()
        
        buid_path.mkdir(parents=False, exist_ok=True)

        self.entity_paths[buid] = Path(buid_path)

        if reload:
            self.load_entities()

        return buid_path


    def _get_files(self, buid, path, glob, must_contain_buid = False, output_as_str=True):
        files = Path(path).glob(glob)

        if must_contain_buid:
            buid_p = self.BUIDParser(ignore_unknown=False, mode = 'first', warn_empty = False)
            files_sel = [fn for fn in files if (buid_p(fn) == buid)]
            files = files_sel

        def ignore_file(fn):
            return fn in self.ignored_files
        
        files = [fn for fn in files if not ignore_file(fn.name)]
                    
        if output_as_str:
            files = [str(fn) for fn in files]

        return list(files)






class BarelyDBEntity(BarelyDBEntityLegacyInterfaceMixin):
    
    path_converter = None

    @classmethod
    def like(cls, entity):
        ''' Copy constructor for subclasses '''
        return cls(buid=entity.buid_with_component, parent_bdb=entity.bdb)

    def __init__(self, buid, parent_bdb):       
        self.logger = parent_bdb.logger
        self._bdb = parent_bdb
        self.path_converter = parent_bdb.path_converter

        buid_p = self.bdb.BUIDParser(ignore_unknown=False, 
                    mode = 'first', 
                    warn_empty = True, 
                    allow_components=False)            
        self._buid = buid_p(buid)


        buid_ent_p = self.bdb.BUIDParser(ignore_unknown=False, 
                    mode = 'first', 
                    warn_empty = True, 
                    allow_components=False)           

        self._buid_entity = buid_ent_p(buid)


        buid_comp_p = self.bdb.BUIDParser(ignore_unknown=False, 
                    mode = 'first', 
                    warn_empty = False, 
                    allow_components=False)                

        self.component = buid_comp_p.parse_component(buid)

    def __repr__(self):
        try:
            name = f'\'{self.name}\''

            components = self.components
            if len(components) > 6:
                comp = f', {len(components)} components'
            else:
                comp = f', components={components}' if components else ''

        except KeyError:
            name = '<does not exist!>'
            comp = ''

        return f'{self.__class__.__qualname__}(\'{self.buid_with_component}\', {name}{comp})'
    
    def __eq__(self,other):
        return self.buid_with_component == other.buid_with_component

    @property
    def buid(self):
        return self._buid

    @property
    def buid_entity(self):
        return self._buid_entity

    @property
    def buid_with_component(self):
        return self._buid + (f'-{self.component}' if self.component is not None else '')

    @property
    def bdb(self):
        return self._bdb

    @property
    def parent(self):
        return BarelyDBEntity(self.buid_entity, self.bdb)
    
    @property
    def name(self):
        return self.bdb.get_entity_name(self.buid)      

    @property
    def entity_path(self):
        return self.bdb.get_entity_path(self.buid_entity)      

    @property
    def component_path(self):
        return self.bdb.get_component_path(self.buid_entity, self.component)

    @property
    def component_paths(self):
        return self.bdb.get_component_paths(self.buid_entity)      

    @property
    def components(self):
        return list(self.component_paths.keys())

    @property
    def path(self):
        return self.entity_path if self.component is None else self.component_path

    def open_in_explorer(self):
        open_in_explorer(self.path)
        
    def files(self, glob, must_contain_buid = False, output_as_str=True):
        if self.component is None:
            return self.entity_files(glob, must_contain_buid=must_contain_buid, output_as_str=output_as_str)
        else:            
            return self.component_files(glob, must_contain_buid=must_contain_buid, output_as_str=output_as_str)

    def entity_files(self, glob, must_contain_buid = False, output_as_str=True):
        return self.bdb._get_files(self.buid_entity, self.entity_path, glob, must_contain_buid=must_contain_buid, output_as_str=output_as_str)

    def component_files(self, glob, must_contain_buid = False, output_as_str=True):
        return self.bdb._get_files(self.buid_with_component, self.component_path, glob, must_contain_buid=must_contain_buid, output_as_str=output_as_str)




    def resolve_relative_path(self, path):
        base_bath = Path(self.path)

        if type(path) in set([type(''), type(Path())]):
            path_resolved = str(base_bath.joinpath(path).absolute().resolve())
        elif isinstance(path, Sequence):
            return [self.resolve_relative_path(p) for p in path] 
        else:
            raise TypeError('path needs to be str, Path, or Sequence (list etc.)!')

        return path_resolved





    def make_file_manager(self, 
                 raw_path = './', 
                 export_path = './',  
                 export_prefix = '',
                 secondary_data_paths = [],
                 auto_string = True, 
                 auto_remove_duplicates = True,
                 **kwds):
        
        rebase_path = lambda p: self.resolve_relative_path(p)
                
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



    def create_component(self, *, component, name):
        # if component is None:
        #     raise ValueError(f'Cannot create component path if no component is specified ({self.buid_with_component})!')

        component = self.bdb.buid_normalizer.validated_component(component)

        existing_path = self.component_paths.get(component, None)
        if existing_path:
            self.logger.warning(f'Component {component} already exists! {str(existing_path)}')
            return existing_path

        base_bath = self.bdb.get_entity_path(self.buid_entity)
        path_name = f'-{component}'
        if name is not None:
            path_name += f'_{str(name)}'

        component_path = base_bath.joinpath(path_name)
        component_path.mkdir(parents=False, exist_ok=True)            

        self.bdb.load_components(self.buid)

        return component_path






    def has_object(self, object_class, allow_parent=None):
        filename = object_class.file_serializer.resolve_file_from_entity(self, allow_parent=allow_parent)
        return False if filename is None else Path(filename).exists()

    def save_object(self, obj, **kwds):
        filename = obj.save_to_entity(self, **kwds)
        return filename

    def load_object(self, object_class, default=None, fail_to_exception=False, quiet=False):
        obj = None

        try:
            obj = object_class.load_from_entity(self)
        except (FileNotFoundError, KeyError):
            error_msg = f'No {object_class.__qualname__} object found for {self.buid_with_component}!'
            if not quiet:
                self.logger.warning(error_msg)
            if fail_to_exception:
                raise FileNotFoundError(error_msg)

        if obj is None and default is not None:
            if not quiet:
                self.logger.warning(f'Using default object!')
            obj = copy.copy(default)
            
        return obj




