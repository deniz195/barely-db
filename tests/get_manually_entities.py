import os
from pathlib import Path

def get_all_entity(path, mode):
    if mode == 'name':
        return get_all_entity_name(path)
    else:
        return get_all_entity_paths(path)

def get_all_entity_name(path):
    path_of_headfolders= [f.path for f in os.scandir(path) if f.is_dir() ]
    all_pairs = dict()
    for head_folder in path_of_headfolders:
        if (os.path.basename(head_folder)!='__code'):
                sub_names = [f.name for f in os.scandir(head_folder) if f.is_dir() ]
                sub_paths = [f.path for f in os.scandir(head_folder) if f.is_dir() ]
                pairs = dict(zip(sub_names,sub_paths))
                all_pairs.update(pairs)
    return list(all_pairs.keys())


def get_all_entity_paths(path):
    path_of_headfolders= [f.path for f in os.scandir(path) if f.is_dir() ]
    all_pairs = dict()
    for head_folder in path_of_headfolders:
        if (os.path.basename(head_folder)!='__code'):
                sub_names = [f.name for f in os.scandir(head_folder) if f.is_dir() ]
                sub_paths = [f.path for f in os.scandir(head_folder) if f.is_dir() ]
                pairs = dict(zip(sub_names,sub_paths))
                all_pairs.update(pairs)
    return list(all_pairs.values())