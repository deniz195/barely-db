# elan == electroanalytical methods

import os
import cProfile
import logging

import pandas as pd
import numpy as np
import json
import re
import zipfile
from pathlib import Path

from enum import Enum, IntEnum

# from chunked_object import *
# from message_dump import *

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

    
    
    
    

class FileManager(object):
    def __init__(self, raw_path = './RAW', 
                 export_path = './export',  
                 export_prefix = '',
                 secondary_data_paths = [],
                 auto_string = True, 
                 auto_remove_duplicates = True):
        
        self.set_raw_path(raw_path)
        self.set_export_path(export_path, export_prefix)
        self.set_secondary_data_paths(secondary_data_paths)
        self.auto_string = auto_string
        self.auto_remove_duplicates = auto_remove_duplicates
        
    def set_raw_path(self, raw_path):
        if not isinstance(raw_path, list):
            raw_path = [raw_path]

        self.raw_path = [Path(p) for p in raw_path]

        for p in self.raw_path:
            if not p.exists():
                raise FileNotFoundError(str(p))        
        
    def set_export_path(self, export_path, export_prefix = ''):
        self.export_prefix = export_prefix
        self.export_path = Path(export_path)
        self.export_path.mkdir(parents=True, exist_ok=True)

    def set_secondary_data_paths(self, secondary_data_paths):
        if not isinstance(secondary_data_paths, list):
            secondary_data_paths = [secondary_data_paths]

        self.secondary_data_paths = [Path(p) for p in secondary_data_paths]        

        for p in self.secondary_data_paths:
            if not p.exists():
                raise FileNotFoundError(str(p))        

    def add_secondary_data_paths(self, secondary_data_paths):
        if not isinstance(secondary_data_paths, list):
            secondary_data_paths = [secondary_data_paths]

        new_paths = self.secondary_data_paths + secondary_data_paths
        self.set_secondary_data_paths(new_paths)       
            
    def _get_files(self, file_glob, paths):
        from itertools import product
        
        if not isinstance(file_glob, list):
            file_glob = [file_glob]

        fns = []
        for p, g in product(paths, file_glob):
            fns += list(p.glob(g))
            
        if self.auto_string: 
            fns = [str(f) for f in fns]
        
        if self.auto_remove_duplicates:
            fns = self.remove_gdrive_duplicates(fns)
        
        return fns

    def get_files(self, file_glob):
        return self._get_files(file_glob, self.raw_path)   
    
    def get_export_files(self, file_glob):
        all_secondary_paths = [self.export_path] + self.secondary_data_paths
        return self._get_files(file_glob, all_secondary_paths)   
       
    def remove_gdrive_duplicates(self, fns):
        # remove stupid google drive duplicates
        fns_filtered = [fn for fn in fns if not bool(re.findall(' \(1\)', fn))]
        return fns_filtered.copy()     

    def _get_valid_filename(self, fn):
        # fn = str(fn).strip().replace(' ', '_')
        return re.sub(r'[\\/:"*?<>|]+', '', fn)

    def make_export_file_name(self, base_file, extension = '', absolute=True):
        bfn = Path(base_file)
        
        fn = self.export_prefix + bfn.name + extension
        fn_val = self._get_valid_filename(fn)
        if fn_val != fn:
            fn = fn_val
            module_logger.warn('Filename has been regularized! (%s)' % fn)

        exp_fn = Path(self.export_path, fn)
        if absolute:
            exp_fn = exp_fn.absolute()
        exp_fn = str(exp_fn)        
            
        if not self.auto_string: 
            exp_fn = Path(exp_fn)
               
        return exp_fn    


class FileNameAnalyzer(object):
    '''
    Extracts information from file names

    Usage example:
    fn_an = elan.FileNameAnalyzer()
    fn_an.add_regex('(CL\d{2,4})', 'cell_type', required=True)
    fn_an.add_regex('CL\d{2,4}-(C\d{1,2})', 'cell_number', required=True)
    fn_an.add_regex('(\d{2,4})degC', 'temp', numeric=True, required=False)
    fn_an.add_regex('(\dp\dV)', 'volt_nom_raw', numeric=False, required=True)

    fn_an.add_prior_knowledge('CL0041-C02', comment='C02 dropped to the floor')
    fn_an.add_prior_knowledge('CL0041-C03', comment='C03 looks nice')

    fn_an.analyze('EE0071b_CL0041-C03_0p8ml-RM261_25degC_0p25C_4p4V_02_GCPL_C03.mpt.x.fc_an.hdf')

    fn_an.test_regex('(CL\d{2,4})')
    fn_an.test_regex('CL\d{2,4}-(C\d{1,2})')

    '''

    def __init__(self):
        self.prio_entries = []
        self.regex_entries = []
        self.logger = module_logger
        self.last_filename = ''
        
    def add_regex(self, regex, param_name, numeric = False, required = True):
        regex_entry = {'regex': regex, 
                       'param_name': param_name, 
                       'numeric': numeric, 
                       'required': required}
        self.regex_entries.append(regex_entry)
        pass

    def add_prior_knowledge(self, match_regex, **kwd):
        prio_entry = {'regex': match_regex, 'values': dict(**kwd)}
        self.prio_entries.append(prio_entry)
        pass

    def analyze(self, filename):
        info = {'filename': filename}
        self.last_filename = filename
        
        info['file_mod_time'] = os.path.getmtime(filename)
        
        for r in self.regex_entries:
            results = re.findall(r['regex'], filename)
            results = list(set(results)) # remove dupplicates!
                        
            if len(results) == 0:
                if r['required']:
                    self.logger.warn('Required parameter (%s) not found!' % r['param_name'])
            elif len(results) >= 1:
                if len(results) > 1:
                    # self.logger.warn('Parameter (%s) ambiguous! Using first of %s.' % (r['param_name'], str(results)))
                    # see if we only look in the filename itself we get uniqueness
                    results_name_only = re.findall(r['regex'], Path(filename).name)
                    results_name_only = list(set(results_name_only)) # remove dupplicates!

                    if len(results_name_only) == 1:
                        results = results_name_only
                    elif len(results_name_only) == 0:
                        self.logger.warn('Parameter (%s) ambiguous in the path, with no info in the filename! This might be a problem. Using first of %s.' % (r['param_name'], str(results)))
                    else:
                        results = results_name_only                        
                        self.logger.warn('Parameter (%s) ambiguous in the filename! This might be a problem. Using first of %s.' % (r['param_name'], str(results)))                   
                    
                if r['numeric']:
                    info[r['param_name']] = float(results[0])
                else:
                    info[r['param_name']] = results[0]
                
        for p in self.prio_entries:
            if re.findall(p['regex'], filename):
                # self.logger.debug('Parameter (%s) matches %s!' % (p['regex'], filename))                
                info.update(p['values'])               
        
        return info

    def test_regex(self, regex, filename = None):
        if filename is None:
            filename = self.last_filename
        
        self.last_filename = filename
        self.logger.info('Using %s' % filename)

        result =  re.findall(regex, filename)

        self.logger.info('%s yields %s' % (regex, str(result)))

        return result
    
    def add_battrion_defaults(self):
        self.add_regex('(EE\d{2,4})', 'experiment_number', required=True)
        self.add_regex('(EE\d{2,4}[a-zA-Z]?)', 'experiment_number_sub', required=False)
        self.add_regex('(CL\d{2,4})', 'cell_type', required=False)
        self.add_regex('CL\d{2,4}-(C\d{1,2})', 'cell_number', required=False)
        self.add_regex('(CL\d{2,4}-C\d{1,2})', 'cell_number_full', required=False)
        self.add_regex('(\d{2,4})degC', 'temp', numeric=True, required=False)
        self.add_regex('([6-9]\d)degC', 'temp_cutoff', numeric=True, required=False)
        self.add_regex('(\dp\dV)', 'volt_nom_raw', numeric=False, required=False)
        self.add_regex('(\d{2,4})_MB', 'step_number_mb', numeric=False, required=False)


        
        
        
from ipywidgets import widgets
def copy_files_with_jupyter_button(fns, target_path, dry_run=False, show_button=True):
    def copy_files(button):
        import shutil

        progress = widgets.IntProgress(min=0, max=len(fns), value=0, description='Copying...')
        display(progress)
        
        for fn in fns:
            t_fn = target_path.joinpath(Path(fn).name) 
            if dry_run:
                # print(f'shutil.copyfile({fn}, {t_fn})')    
                pass
            else:
                shutil.copyfile(fn, t_fn)    
            progress.value += 1
        
        progress.description = 'Done!'

    
    button = widgets.Button(description = f'Copy files ({len(fns)}) to {target_path}',
                           layout=widgets.Layout(width='90%')
                           )
    button.on_click(copy_files)
    
    if show_button:
        display(button)
    else:
        copy_files(button)
                