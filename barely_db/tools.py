import logging
import shutil

from pathlib import Path

from . import BarelyDB

__all__ = ['BarelyDBChecker', 'BarelyDBSyncer']

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


class BarelyDBChecker(object):

    _bdb = None

    def __init__(self, bdb):
        self.bdb = bdb

    @property
    def bdb(self):
        return self._bdb

    @bdb.setter
    def bdb(self, value):
        self._bdb = value

    

    def _discover_files(self, glob):
        ''' Iterate over all files in the database that match glob. '''

        for buid in self.bdb.entities:
            ent = self.bdb.get_entity(buid)
            fns = ent.get_entity_files(glob)
            
            for fn in fns:
                # if directories_only
                yield ent.buid, fn
            
            comps = ent.get_component_paths()
            for component in comps:
                fns = ent.get_component_files(glob, component=component)
                for fn in fns:
                    yield f'{ent.buid}-{component}', fn

    
    def discover_files(self, glob, dependent_files_resolver=None):
        ''' Iterate over all files in the database that match glob. Resolve
            dependent files if necessary.'''

        diter = self._discover_files(glob)
        
        if dependent_files_resolver is None:
            final_diter = diter
        else:
            def resolve_dep_files(diter):
                for buid, fn in diter:
                    yield buid, fn
                    for dep_fn in dependent_files_resolver(fn):
                        yield buid, dep_fn
            
            final_diter = resolve_dep_files(diter)
        
        return final_diter




class BarelyDBSyncer(object):
    _bdb_source = None
    _bdb_target = None
    _dry_run = True
    
    @property
    def bdb_source(self):
        return self._bdb_source

    @property
    def bdb_target(self):
        return self._bdb_target
    
    @property
    def dry_run(self):
        return self._dry_run
    
    @dry_run.setter
    def dry_run(self, value):
        self.logger.info(f'Setting dry run to {value}!')
        self._dry_run = value
    
    def __init__(self, bdb_source, bdb_target=None, dependent_files_resolver=None):
        self._bdb_source = bdb_source
        self._bdb_target = bdb_target
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.dependent_files_resolver = dependent_files_resolver
        
    def make_new_target_bdb(self, new_base_path):
        module_logger.info(f'Making new bdb at {new_base_path}')
        new_base_path.mkdir(parents=True, exist_ok=True)
        bdb_target = BarelyDB(base_path=new_base_path, path_depth=self.bdb_source.path_depth)
        self._bdb_target = bdb_target
        return bdb_target
        
    def get_relative_source_path(self, abs_path):
        return Path(abs_path).relative_to(self.bdb_source.base_path)

    def get_absolute_target_path(self, rel_path):
        return Path(self.bdb_target.base_path).joinpath(rel_path)

    def translate_path_to_target(self, source_path):
        rel_path = self.get_relative_source_path(source_path)
        return self.get_absolute_target_path(rel_path)
    
    def mkdir_from_source(self, source_path):
        new_path = self.translate_path_to_target(source_path)
        
        if self.dry_run:
            self.logger.debug(f'[dryrun] Create {new_path}')
        else:
            new_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f'Create {new_path}')
            
        return new_path

    def copy_file_from_source(self, source_path):
        new_path = self.translate_path_to_target(source_path)
        
        try:
            if self.dry_run:
                if not Path(source_path).exists():
                    raise FileNotFoundError(f'File does not exists {source_path}')
                self.logger.debug(f'[dryrun] Copy to {new_path}')
            else:
                self.logger.debug(f'Copy to {new_path}')
                parent = Path(new_path).parent
                if not parent.exists():
                    self.logger.debug(f'Making directory {parent}')
                    parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(source_path, new_path)
        except FileNotFoundError as e:
            self.logger.error(e)
            
            
        return new_path

    
    def copy_buid_types(self):
        # create types
        source_buid_type_paths = self.bdb_source.buid_type_paths        
        self.bdb_target.buid_type_paths = {k: self.mkdir_from_source(path) for k, path in source_buid_type_paths.items()}
        
    def copy_entities(self, copy_components=True):
        counter = 0
        for buid, path in self.bdb_source.entity_paths.items():
            self.mkdir_from_source(path)
            counter += 1

            if copy_components:
                ent = self.bdb_source.get_entity(buid)
                comp_paths = ent.get_component_paths()
                for comp_buid, comp_path in comp_paths.items():
                    self.mkdir_from_source(comp_path)
                    counter += 1

        self.logger.info(f'Created {counter} directories')


    def copy_files(self, glob, dependent_files_resolver=None):
        if dependent_files_resolver is None:
            dependent_files_resolver = self.dependent_files_resolver

        bc = BarelyDBChecker(self.bdb_source)
        diter = bc.discover_files(glob, dependent_files_resolver=dependent_files_resolver)

        counter = 0
        for buid, fn in diter:
            new_fn = self.copy_file_from_source(fn)
            counter += 1
            
        self.logger.info(f'Copied {counter} files')
            

    def copy_all(self, glob='*.yaml'):
        self.copy_buid_types()
        self.copy_entities()

        self.copy_files('*.yaml', dependent_files_resolver=self.dependent_files_resolver)
        self.bdb_target.load_entities()
        







    
