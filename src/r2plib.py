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
import pyPreservica as PRES

path_to_file = TY.Union[str, PL.Path]
path_to_dir = path_to_file


def create_package(bagit_dir: path_to_dir, parent_folder: str) -> path_to_file:
    """Create a XIPv6 package (zip file) from the files in 'bagit_dir'
    and returns the path to the package"""

    path_files = []
    for root, dirs, files in os.walk(bagit_dir):
        path_files.extend(os.path.join(root, file) for file in files)

    package_path = PRES.complex_asset_package(
        preservation_files_list=path_files,
        parent_folder=parent_folder,
        Preservation_files_fixity_callback=PRES.Sha256FixityCallBack(),
        export_folder="packages",
    )

    return package_path


def create_zipfile(bagit_path_to_dir: path_to_dir) -> str:
    """Create a zipfile with the content of 'bagit_path_to_dir', where
    bagit_path_to_dir is the full path to the folder.

    Returns the name of the zipfile
    """
    bagit_dir = bagit_path_to_dir.name
    zipfile = f"{bagit_dir}.zip"
    zf = ZIP.ZipFile(zipfile, "w")
    # print(f"Bagit_dir: '{bagit_dir}'")
    for dirname, subdirs, files in OS.walk(bagit_dir):
        # print(f"dirname: '{dirname}'")
        zf.write(dirname)
        for ff in files:
            if ff == "bagit.txt":
                add_comment(dirname, ff)
                zf.write(OS.path.join(dirname, ff))
                remove_comment(dirname, ff)
            else:
                zf.write(os.path.join(dirname, ff))
    zf.close()

    return zipfile


def save_metadata(bagit_dir: path_to_dir) -> str:
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
    xip_package: str


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
        xip_package=folders.get("xip_package", "zip"),
    )

    return folder


def get_subdirs(data_dir: path_to_dir) -> TY.List[path_to_file]:
    """Returns a list of subdirectories of the 'data_dir' folder."""

    subdirs = []

    subdirs = [dir for dir in data_dir.iterdir() if dir.is_dir()]
    return subdirs


def load_sha_repo(dir: path_to_file) -> list:
    """
    Return a list with files and checksum for each file in 'dir'
    """

    file_name = dir.joinpath("sha1.txt")

    with open(file_name, "r") as ff:
        text = ff.readlines()

    return [line.strip().split()[3:] for line in text if len(line) > 1]


def pres_checksum(entity, folder_name):
    """
    Query Preservica object 'entity' for the 'folder_name', and return a dictionary with the filename and SHA1 checksum.
    """

    pres_items_sha = {}

    for ee in entity.identifier("code", folder_name):
        ee_child = entity.children(ee.reference)
        if ee_child.get_total() > 1:
            # This is the 'reference' folder with all the files.
            for cc in ee_child.results:
                if cc.entity_type == PRES.EntityType.ASSET:
                    asset = entity.asset(cc.reference)
                    for bitstream in entity.bitstreams_for_asset(asset):
                        for algorithm, value in bitstream.fixity.items():
                            pres_items_sha.update({bitstream.filename: value})
                elif cc.entity_type == PRES.EntityType.FOLDER:
                    data_children = entity.children(cc.reference)
                    for dd in data_children.results:
                        dd_asset = entity.asset(dd.reference)
                        for bb in entity.bitstreams_for_asset(dd_asset):
                            for algorithm, value in bb.fixity.items():
                                pres_items_sha.update(
                                    {f"{cc.title}/{bb.filename}": value}
                                )

    return pres_items_sha


def repo_checksum(folder_name):
    """
    Read the file 'sha1.txt' inside folder 'folder_name', and return a dictionary with file names and checksum.
    """

    repo_items_sha = {}

    # Read content of 'sha1.txt'
    with open(PL.Path(folder_name).joinpath("sha1.txt")) as ff:
        text = ff.readlines()
    text = [line.strip().split()[3:] for line in text if len(line) > 1]
    for line in text:
        repo_path_list, repo_sha = line[0].split("/"), line[1]
        bag_dir_pos = repo_path_list.index(folder_name) + 1
        repo_items = repo_path_list[bag_dir_pos:]
        # print(f"{'/'.join([ii for ii in repo_items])} {repo_sha}")
        repo_item = f"{'/'.join([ii for ii in repo_items])}"
        repo_items_sha.update({repo_item: repo_sha})

    return repo_items_sha
