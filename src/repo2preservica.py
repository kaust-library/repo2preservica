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
    else:
        LOG.warning("No parent folder was declared in config file.")
        parent = None

    num_submissions = 0

    old_dir = PL.Path.cwd()
    OS.chdir(folder.data_folder)

    bagit_dirs = R2P.get_subdirs(str(PL.Path.cwd()))

    LOG.info(f"Start of bagging process.")
    LOG.info(
        f"We found {len(bagit_dirs)} {len(bagit_dirs) > 1 and 'folders' or 'folder'} to scan"
    )
    for bag_dir in bagit_dirs:

        if num_submissions >= folder.max_submissions:
            LOG.warning(f"NUmber of submissions exceed {folder.max_submissions}")
            break

        LOG.info(f"Scanning folder '{bag_dir}'")
        # To avoid problems we will work with the string
        # representation of pathlib object
        str_bag = str(bag_dir.name)

        # Save metadata to file <str_bag>.metadata
        metadata_path = R2P.save_metadata(str_bag)
        LOG.info(f"Created metadata file '{metadata_path}'")
        result = entity.identifier("code", str_bag)
        LOG.info(f"Results: '{len(result)}'")
        if len(result) == 0:
            zipfile = R2P.create_zipfile(bag_dir)
            OS.remove(metadata_path)

            LOG.info(f"Uploading {bag_dir} to S3 bucket {folder.bucket}")
            upload.upload_zip_package_to_S3(
                path_to_zip_package=zipfile,
                bucket_name=folder.bucket,
                callback=PRES.UploadProgressConsoleCallback(zipfile),
                delete_after_upload=True,
            )

        # Change to directory with data for bagging them
        # OS.chdir(str_bag)


if __name__ == "__main__":
    main()
