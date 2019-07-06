import logging

__all__ = ['BarelyDBChecker', ]

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

    

    def discover_files(self, glob):
        ''' Iterate over all files in the database that match glob. '''

        for buid in self.bdb.entities:
            ent = self.bdb.get_entity(buid)
            fns = ent.get_entity_files(glob)
            
            for fn in fns:
                yield ent.buid, fn
            
            comps = ent.get_component_paths()
            for component in comps:
                fns = ent.get_component_files(glob, component=component)
                for fn in fns:
                    yield f'{ent.buid}-{component}', fn








    
