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
from .parser import *
from .file_management import *

# from .tools import *

__all__ = ['BarelyDB', 'BarelyDBConfig', 'BarelyDBSystemConfig', 'BarelyDBEntity', 'FileManager', 'FileNameAnalyzer', 'serialize_to_file', 'open_in_explorer', 'ClassFileSerializer']

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


@attr.s(frozen=True, kw_only=True)
class BarelyDBSystemConfig:
    default_base_path = attr.ib(factory=dict, type=typing.Dict[str, typing.List[str]])

    @classmethod
    def from_legacy_default(cls):
        return cls(default_base_path = {\
            "battrion_manufacturing":
                    [\
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
            }
        )
    

    @classmethod
    def get_file(cls):
        filename = '.bdb_system_config.json'

        user_config_file = str(Path.home().joinpath(filename))
        return user_config_file

    def save(self, config_file=None):
        if config_file is None:
            config_file = self.get_file()        

        self_dict = attr.asdict(self)

        with open(config_file, 'w') as f:
            json.dump(self_dict, f, indent=4)

    @classmethod
    def load(cls, config_file=None, default_to_empty=False):
        if config_file is None:
            config_file = cls.get_file()        

        try:
            with open(config_file, 'rb') as f:
                self_dict = json.load(f)

            return cattr.structure(self_dict, cls)
        
        except FileNotFoundError as e:
            if default_to_empty:
                module_logger.warning(f'Could not load {config_file}!')
                return cls()
            else:
                raise
        


@attr.s(frozen=True, kw_only=True)
class BarelyDBConfig:

    name = attr.ib(default='master', type=str)

    path_depth = attr.ib(default=0)
    known_bases = attr.ib(factory=list, type=typing.List[str])
    ignored_files = attr.ib(factory=list, type=typing.List[str])
    auto_reload_components = attr.ib(default=None)
    buid_types = attr.ib(factory=dict, type=typing.Dict[str, str])

    @staticmethod
    def resolve_file(base_path):
        base_path = Path(base_path)
        
        if base_path.is_dir():
            config_file = base_path.joinpath('bdb_config.json')
        else:
            config_file = base_path

        return str(config_file)

    def save(self, base_path):
        config_file = self.resolve_file(base_path)

        self_dict = attr.asdict(self)

        with open(config_file, 'w') as f:
            json.dump(self_dict, f, indent=4)

    @classmethod
    def load(cls, base_path):
        config_file = Path(cls.resolve_file(base_path))

        with open(config_file, 'rb') as f:
            self_dict = json.load(f)

        return cattr.structure(self_dict, cls)

    @classmethod
    def from_legacy_default(cls):
        return cls(
            name='battrion_manufacturing',
            path_depth = 1,
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
        ],
        ignored_files = ['desktop.ini'],
        auto_reload_components = None,
        buid_types = {\
            'slurry': 'SL',
            'web': 'WB',
            'cells': 'CL',
            'electrochemistry': 'EE',
            'rawmaterial': 'RM',
            'experiment': 'EXP',
            'equipment': 'EQ',
            'manufacturing_orders': 'MO',
            'product': 'PD',
            'documents': 'DOC',
        }                   
                  )
    

class BarelyDB(object):
    config = None
    base_path = None

    auto_reload_components = None

    buid_type_paths = None

    _MyBUIDParser = None

    def __init__(self, name=None, base_path=None, path_depth=None, auto_reload_components = True):
        self.logger = module_logger

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
        self.base_path = self.base_path.resolve().absolute()

        self.entity_paths = {}
        self.entity_properties = {}
        self.component_paths = {}

        self._MyBUIDParser = BUIDParser.create_class(self.config.buid_types)

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
            self.logger.error(f'Following entities have multiple paths/folders: {duplicate_buid}')

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


    def load_components(self, buid):
        entity_path = self.get_entity_path(buid)
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



    def get_entity_path(self, buid):
        buid = self.buid_normalizer(buid)
        path = self.entity_paths[buid]
        path = path.resolve().absolute()
        return path
    
    def get_entity_name(self, buid):
        path = self.get_entity_path(buid)
        return Path(path).parts[-1]

    def get_component_paths(self, buid):
        buid = self.buid_normalizer(buid)
        if self.auto_reload_components or (buid not in self.component_paths):
            self.load_components(buid)
                       
        paths = self.component_paths[buid]
        paths = {comp: Path(path).resolve().absolute() for comp, path in paths.items()}
        return paths

    def get_component_path(self, buid, component):
        component_paths = self.get_component_paths(buid)
        
        if component in component_paths:
            return component_paths[component]    
        else:
            raise FileNotFoundError(f'No path for component {component} in {buid}!')


    def get_free_buid(self, start_buid, no_buids = 1, no_free_biuds=None):
        buid_p = self.BUIDParser()

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
        

    def create_entity_path(self, buid, comment, reload=True):       
        buid = self.buid_normalizer(buid)
        buid_type = self.buid_normalizer.parse_type(buid)

        try:
            buid_path = self.get_entity_path(buid)
            return buid_path
        except KeyError:
            # entity does not exist
            pass

        # create new path
        buid_base_path = Path(self.buid_type_paths[buid_type])
        buid_path = buid_base_path.joinpath(f'{buid}_{comment}')

        buid_path = buid_path.resolve().absolute()
        
        buid_path.mkdir(parents=False, exist_ok=True)

        if reload:
            self.load_entities()

        return buid_path



    def _get_files(self, buid, path, glob, must_contain_buid = False, output_as_str=True):
        files = path.glob(glob)

        def ignore_file(fn):
            return fn in self.ignored_files
        
        if must_contain_buid:
            buid_p = self.BUIDParser(ignore_unknown=False, mode = 'first', warn_empty = False)
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

    def get_entity(self, buid):
        return BarelyDBEntity(buid, self)





class BarelyDBEntity(object):

    @classmethod
    def like(cls, entity):
        ''' Copy constructor for subclasses '''
        return cls(buid=entity.buid_with_component, parent_bdb=entity.bdb)

    def __init__(self, buid, parent_bdb):       
        self.logger = module_logger

        self._bdb = parent_bdb

        buid_p = self.bdb.BUIDParser(ignore_unknown=False, 
                    mode = 'first', 
                    warn_empty = True, 
                    allow_components=False)            
        self._buid = buid_p(buid)

        buid_comp_p = self.bdb.BUIDParser(ignore_unknown=False, 
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

    def get_entity_path(self):
        return self.bdb.get_entity_path(self.buid)      

    def open_entity_path(self):
        if self.component is None:
            open_in_explorer(self.get_entity_path())
        else:
            open_in_explorer(self.get_component_path())

    def get_entity_name(self):
        return self.bdb.get_entity_name(self.buid)      

    def get_entity_files(self, glob, must_contain_buid = False, output_as_str=True):
        return self.bdb.get_entity_files(self.buid, glob, must_contain_buid=must_contain_buid, output_as_str=output_as_str)

    def get_component_files(self, glob, component=None, must_contain_buid = False, output_as_str=True):
        if component is None:
            component = self.component

        return self.bdb.get_component_files(self.buid, component, glob, must_contain_buid=must_contain_buid, output_as_str=output_as_str)

    def get_component_paths(self):
        return self.bdb.get_component_paths(self.buid)      
        
    def get_component_path(self, component=None):
        if component is None:
            component = self.component

        return self.bdb.get_component_path(self.buid, component)

    def component_files(self, glob, must_contain_buid = False, output_as_str=True, component=None):
        if component is None:
            component = self.component
        
        buid = self.buid_normalizer(buid)        
        path = self.get_entity_path(buid)
        files = path.glob(glob)

        def ignore_file(fn):
            return fn in self.ignored_files
        
        if must_contain_buid:
            buid_p = self.bdb.BUIDParser(ignore_unknown=False, mode = 'first', warn_empty = False)
            files_sel = [fn for fn in files if (buid_p(fn) == buid)]
            files = files_sel

        files = [fn for fn in files if not ignore_file(fn.name)]
                    
        if output_as_str:
            files = [str(fn) for fn in files]

        return list(files)



    def has_object(self, object_class, allow_parent=None):
        filename = object_class.file_serializer.resolve_file_from_entity(self, allow_parent=allow_parent)
        if filename is None:
            return False
        else:
            return Path(filename).exists()

    def load_object(self, object_class, default=None, fail_to_exception=False, quiet=False):
        try:
            obj = None
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

    def save_object(self, obj, **kwds):
        filename = obj.save_to_entity(self, **kwds)

        return filename
