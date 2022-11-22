#
# Ingest the files from the repository into Preservica
#
import click as CL
import dotenv as DOT
import pyPreservica as PRES
import r2plib as R2P
import logging as LOG
import os as OS

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

    bagit_dirs = R2P.get_subdirs(folder.data_folder)

    num_submissions = 0


    for bag_dir in bagit_dirs:

        # To avoid problems we will work with the string 
        # representation of pathlib object 
        str_bag = str(bag_dir)

        print(f"bag_dir: {bag_dir}")
        # Change to directory with data for bagging them
        #OS.chdir(str_bag)







        #
        #Return the old dir
        #OS.chdir(old_dir)


if __name__ == "__main__":
    main()


