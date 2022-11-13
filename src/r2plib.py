#
# Library of functions for 'repo2preservica' script

import os
import collections as CC
import configparser as CONF
from pydantic import BaseModel

class Folder(BaseModel):
    '''configure the folders on the local file system and on Preservica '''
    parent_folder_id: str = None
    data_folder: str = None
    bucket: str = None
    max_submissions: int = 10
    security_tag: str = 'open'


def read_config(input_file: str) -> Folder:
    '''Read input file and return the folders (path) to ingest into Preservica'''
    config = CONF.ConfigParser()
    config._interpolation = CONF.ExtendedInterpolation()
    config.read(input_file)

    folders = config['FOLDERS']
    parent_folder_id = folders.get('parent_folder')
    data_folder = folders.get('data_folder')
    bucket = folders.get('bucket')
    max_submissions = folders.getint('max_submissions', 10)
    security_tag = folders.get('security_tag', 'open')

    folder = Folder()

    return folder
 