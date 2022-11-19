#
# Ingest the files from the repository into Preservica
#
import click as CL
import dotenv as DOT
import pyPreservica as PRES
import r2plib as R2P
import logging as LOG

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

    sub_dirs = R2P.get_subdirs(folder.data_folder)

    for dir in sub_dirs:
        LOG.info(f"Scanning folder '{dir}' for ingestion")
        entities = entity.identifier("code", str(dir))
        LOG.info(f"Checking number of entries: {len(entities)}")
        if len(entities) == 0:
            LOG.info(f"Creating folder '{dir}' in Preservica entity")
            # Using the string representation of 'dir' because pyPreservica can't
            # handle Pathlib objects yet.
            str_dir = str(dir)
            folder_preservica = entity.create_folder(str_dir, str_dir, 
                folder.security_tag, parent.reference)
            entity.add_identifier(folder_preservica, "code", str_dir)
            dir_l1_ref = folder_preservica.reference
        else:
            folder_preservica = entities.pop()
            dir_l1_ref = folder_preservica.reference

if __name__ == "__main__":
    main()


