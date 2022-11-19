#
# Library of functions for 'repo2preservica' script

import os
import collections as CC
import configparser as CONF
from pydantic import BaseModel
import pathlib as PL

class Folder(BaseModel):
    '''configure the folders on the local file system and on Preservica '''
    parent_folder_id: str = ""
    data_folder: str = ""
    bucket: str = ""
    max_submissions: int = 10
    security_tag: str = 'open'


def read_config(input_file: str) -> Folder:
    '''Read input file and return the folders (path) to ingest into Preservica'''
    config = CONF.ConfigParser()
    config._interpolation = CONF.ExtendedInterpolation()
    config.read(input_file)

    folder = Folder()

    folders = config['FOLDERS']
    folder.parent_folder_id = folders.get('parent_folder')
    folder.data_folder = folders.get('data_folder')
    folder.bucket = folders.get('bucket')
    folder.max_submissions = folders.getint('max_submissions', 10)
    folder.security_tag = folders.get('security_tag', 'open')

    return folder
 
def get_subdirs(data_dir: str) -> list:
    '''Returns a list of subdirectories of the 'data_dir' folder.'''

    root_dir = PL.Path(data_dir)
    subdirs = []

    subdirs = [dir for dir in root_dir.iterdir() if dir.is_dir()]
    return subdirs

