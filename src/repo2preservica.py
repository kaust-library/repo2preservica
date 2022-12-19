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


@CL.command()
@CL.argument("input", type=CL.File("r"))
def main(input):

    LOG.basicConfig(encoding="utf-8", level=LOG.INFO)

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
        parent_ref = parent.reference
    else:
        LOG.warning("No parent folder was declared in config file.")
        parent = None

    num_submissions = 0

    old_dir = PL.Path.cwd()
    OS.chdir(folder.data_folder)

    bagit_dirs = R2P.get_subdirs(PL.Path.cwd())

    LOG.info(f"Start of bagging process.")
    LOG.info(
        f"We found {len(bagit_dirs)} {len(bagit_dirs) > 1 and 'folders' or 'folder'} to scan"
    )
    for bagit_dir in bagit_dirs:

        if num_submissions >= folder.max_submissions:
            LOG.warning(f"NUmber of submissions exceed {folder.max_submissions}")
            break

        # 'bagit_dir' is the full path to the folder, but we want only
        # the name.
        bagit_name = bagit_dir.name

        # Check if 'bagit_dir' exists in Preservica
        bagit_identifier = entity.identifier("code", bagit_name)
        if len(bagit_identifier) == 0:
            # Creating the folder
            LOG.info(f"Creating Preservica folder '{bagit_name}'")
            bagit_folder_preservica = entity.create_folder(
                bagit_name, bagit_name, folder.security_tag, parent_ref
            )
            entity.add_identifier(bagit_folder_preservica, "code", bagit_name)
            bagit_preserv_ref = bagit_folder_preservica.reference

            # Preparing content for upload
            LOG.info(f"Creating metadata file for '{bagit_name}'")
            metadata_path = R2P.save_metadata(bagit_name)
            LOG.info(f"Creating zip with folder '{bagit_name}' content")
            zipfile = R2P.create_zipfile(bagit_dir)
            LOG.info(f"Removing metadata file '{metadata_path}'")
            OS.remove(metadata_path)

            LOG.info(f"Uploading {bagit_dir} to S3 bucket {folder.bucket}")
            upload.upload_zip_package_to_S3(
                path_to_zip_package=zipfile,
                bucket_name=folder.bucket,
                callback=PRES.UploadProgressConsoleCallback(zipfile),
                delete_after_upload=True,
                folder=bagit_preserv_ref,
            )

        else:
            LOG.info(f"Preservica folde '{bagit_name}' already exists")
            LOG.info("Skipping folder")
            bagit_folder_preservica = bagit_identifier.pop()
            # bagit_preserv_ref = bagit_folder_preservica.reference


if __name__ == "__main__":
    main()
