#
# Library of functions for 'repo2preservica' script

import os
import collections as CC
import configparser as CONF
from pydantic import BaseModel
import pathlib as PL
import typing as TY

path_to_file = TY.Union[str, PL.Path]

class Folder(BaseModel):
    '''configure the folders on the local file system and on Preservica '''
    parent_folder_id: str
    data_folder: str
    bucket: str
    max_submissions: int
    security_tag: str


def read_config(input_file: str) -> Folder:
    '''Read input file and return the folders (path) to ingest into Preservica'''
    config = CONF.ConfigParser()
    config._interpolation = CONF.ExtendedInterpolation()
    config.read(input_file)

    folders = config['FOLDERS']
    folder = Folder(
        parent_folder_id = folders.get('parent_folder'), 
        data_folder = folders.get('data_folder'),
        bucket = folders.get('bucket'),
        max_submissions = folders.getint('max_submissions', 10),
        security_tag = folders.get('security_tag', 'open')
    )

    return folder
 
def get_subdirs(data_dir: str) -> list[path_to_file]:
    '''Returns a list of subdirectories of the 'data_dir' folder.'''

    root_dir = PL.Path(data_dir)
    subdirs = []

    subdirs = [dir for dir in root_dir.iterdir() if dir.is_dir()]
    return subdirs

