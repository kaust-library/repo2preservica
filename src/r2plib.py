#
# Library of functions for 'repo2preservica' script

import os
import collections as CC
import configparser as CONF
from pydantic import BaseModel
import pathlib as PL
import typing as TY
import os as OS
import zipfile as ZIP

path_to_file = TY.Union[str, PL.Path]
dir_path = path_to_file


def create_zipfile(bagit_dir: dir_path) -> str:
    zipfile = f"{bagit_dir}.zip"
    zf = ZIP.ZipFile(zipfile, "w")
    for dirname, subdirs, files in OS.walk(bagit_dir):
        zf.write(dirname)
        for ff in files:
            if ff == "bagit.txt":
                add_comment(dirname, ff)
                zf.write(OS.path.join(dirname, ff))
                remove_comment(dirname, ff)
            else:
                zf.write(dirname, ff)
    zf.close()

    return zipfile


def save_metadata(bagit_dir: str) -> str:
    """Save metatada to a file name <bagit_dir>.metadata"""

    title = bagit_dir
    description = bagit_dir

    metadata_text = """<DeliverableUnit xmlns="http://www.tessella.com/XIP/v4">
<Title>CATREF</Title>
<ScopeAndContent>SCOPE</ScopeAndContent>
</DeliverableUnit>"""
    metadata_text = metadata_text.replace("CATREF", title)
    metadata_text = metadata_text.replace("SCOPE", description)
    metadata_file = f"{bagit_dir}.metadata"
    metadata_path = OS.path.join(bagit_dir, metadata_file)
    with open(metadata_path, encoding="utf-8", mode="wt") as fmeta:
        fmeta.write(metadata_text)

    return metadata_path


def add_comment(dirname, filename):
    file = OS.path.join(dirname, filename)
    with open(file, encoding="utf-8", mode="rt") as fd:
        lines = fd.readlines()
    lines[0] = f"#{lines[0]}"
    with open(file, encoding="utf-8", mode="wt") as fd:
        fd.writelines(lines)


def remove_comment(dirname, filename):
    file = OS.path.join(dirname, filename)
    with open(file, encoding="utf-8", mode="rt") as fd:
        lines = fd.readlines()
        lines[0] = lines[0].replace("#", "", 1)
    with open(file, encoding="utf-8", mode="wt") as fd:
        fd.writelines(lines)


def fetch_title(dirname, filename, default):
    t = default
    d = default
    file = os.path.join(dirname, filename)
    with open(file, encoding="utf-8", mode="rt") as fd:
        lines = fd.readlines()
    for line in lines:
        if line.startswith("DC_Title:"):
            t = line.replace("DC_Title:", "").strip()
        if line.startswith("DC_description:"):
            d = line.replace("DC_description:", "").strip()
    return t, d


class Folder(BaseModel):
    """configure the folders on the local file system and on Preservica"""

    parent_folder_id: str
    data_folder: str
    bucket: str
    max_submissions: int
    security_tag: str


def read_config(input_file: str) -> Folder:
    """Read input file and return the folders (path) to ingest into Preservica"""
    config = CONF.ConfigParser()
    config._interpolation = CONF.ExtendedInterpolation()
    config.read(input_file)

    folders = config["FOLDERS"]
    folder = Folder(
        parent_folder_id=folders.get("parent_folder"),
        data_folder=folders.get("data_folder"),
        bucket=folders.get("bucket"),
        max_submissions=folders.getint("max_submissions", 10),
        security_tag=folders.get("security_tag", "open"),
    )

    return folder


def get_subdirs(data_dir: str) -> list[path_to_file]:
    """Returns a list of subdirectories of the 'data_dir' folder."""

    root_dir = PL.Path(data_dir)
    subdirs = []

    subdirs = [dir for dir in root_dir.iterdir() if dir.is_dir()]
    return subdirs
