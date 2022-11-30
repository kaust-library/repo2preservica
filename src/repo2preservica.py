#
# Ingest the files from the repository into Preservica
#
import click as CL
import dotenv as DOT
import pyPreservica as PRES
import r2plib as R2P
import logging as LOG
import os as OS
import pathlib as PL
import zipfile as ZIP

metadata_text = """<DeliverableUnit xmlns="http://www.tessella.com/XIP/v4">
<Title>CATREF</Title>
<ScopeAndContent>SCOPE</ScopeAndContent>
</DeliverableUnit>"""


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



@CL.command()
@CL.argument('input', type=CL.File('r'))
def main(input):

    LOG.basicConfig(encoding='utf-8', level=LOG.INFO)

    # Read credentials from the environment variables
    DOT.load_dotenv()

    # Preservica objects
    entity = PRES.EntityAPI()
    upload = PRES.UploadAPI()
    LOG.info(f"Entity: '{entity}'")

    # Read config. file
    folder = R2P.read_config(input.name)

    # Check if the parent folder ID was declared in the config file.
    if folder.parent_folder_id:
        parent = entity.folder(folder.parent_folder_id)
        LOG.info(f"Files will be ingest into '{parent.title}'.")
    else:
        LOG.warning("No parent folder was declared in config file.")
        parent = None


    old_dir = PL.Path.cwd()
    OS.chdir(folder.data_folder)

    bagit_dirs = R2P.get_subdirs(str(PL.Path.cwd()))

    num_submissions = 0

    LOG.info(f"Start of bagging process.")
    LOG.info(f"We found {len(bagit_dirs)} {len(bagit_dirs) > 1 and 'folders' or 'folder'} to scan")
    for bag_dir in bagit_dirs:

        if num_submissions >= folder.max_submissions:
            LOG.warning(f"NUmber of submissions exceed {folder.max_submissions}")
            break

        LOG.info(f"Scanning folder '{bag_dir}'")
        # To avoid problems we will work with the string 
        # representation of pathlib object 
        str_bag = str(bag_dir)

        title = str_bag
        description = str_bag
        result = entity.identifier("code", str_bag)
        LOG.info(f"Results: '{len(result)}'")
        if len(result) == 0:
            metadata_text = metadata_text.replace("CATREF", title)
            metadata_text = metadata_text.replace("SCOPE", description)
            metadata_file = f"{bag_dir}.metadata"

            metadata_path = bag_dir.joinpath(metadata_file)

            with open(metadata_path, encoding='utf-8', mode='wt') as fmeta:
                fmeta.write(metadata_text)

            cur_dir = bag_dir.cwd()
            zipfile = f"{bag_dir}.zip"
            zf = ZIP.ZipFile(zipfile, 'w')
            for dirname, subdirs, files in OS.walk(bag_dir):
                zf.write(dirname)
                for ff in files:
                        if ff == 'bagit.txt':
                            add_comment(dirname,ff)
            zf.close()



        # Change to directory with data for bagging them
        #OS.chdir(str_bag)


        #
        #Return the old dir
        #OS.chdir(old_dir)


if __name__ == "__main__":
    main()
