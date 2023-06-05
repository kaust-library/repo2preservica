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
import pprint as PP
import time as TM


@CL.group()
def repo2pres():
    """Ingestion of institutional repository into Preservica"""


@repo2pres.command()
@CL.option(
    "-i", "--input-folder", type=CL.STRING, help="Folder with the items to ingest"
)
@CL.option("-p", "--parent-folder", type=CL.STRING, help="Preservica parent folder")
# @CL.argument("input", type=CL.Path("r"))
def ingest(input_folder, parent_folder):
    """Ingest items from repository into Preservica"""
    # Python >3.8: LOG.basicConfig(encoding="utf-8", level=LOG.INFO)
    LOG.basicConfig(level=LOG.INFO)
    # Read credentials from the environment variables
    DOT.load_dotenv()

    # Preservica objects
    entity = PRES.EntityAPI()
    upload = PRES.UploadAPI()
    LOG.info(f"Entity: '{entity}'")

    # Read config. file.
    # Note. The term 'collection' is borrowed from the PyPreservica
    # documentation, to reference 'folder,' because it seems the term
    # 'folder' already is used by the Upload API.
    input = "repo2preservica.cfg"
    collection = R2P.read_config(input)

    CL.echo(f"input folder: {input_folder}")

    # Overwrite the values from the config file with
    # parameters from the command line (if provided.)
    if input_folder:
        collection.data_folder = input_folder
    if parent_folder:
        collection.parent_folder_id = parent_folder

    # Check if the parent collection ID was declared in the config file.
    if collection.parent_folder_id:
        parent = entity.folder(collection.parent_folder_id)
        LOG.info(f"Files will be ingest into '{parent.title}'.")
        parent_ref = parent.reference
    else:
        LOG.warning("No parent collection was declared in config file.")
        parent = None

    num_submissions = 0

    old_dir = PL.Path.cwd()
    OS.chdir(collection.data_folder)

    bagit_dirs = R2P.get_subdirs(PL.Path.cwd())

    LOG.info(f"Start of bagging process.")
    LOG.info(
        f"We found {len(bagit_dirs)} {len(bagit_dirs) > 1 and 'folders' or 'folder'} to scan"
    )
    uploaded_folders = []
    for bagit_dir in bagit_dirs:
        # Remove the folders that were skipped, and keep only the ones that
        # were uploaded
        if num_submissions >= collection.max_submissions:
            LOG.warning(f"NUmber of submissions exceed {collection.max_submissions}")
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
                bagit_name, bagit_name, collection.security_tag, parent_ref
            )
            entity.add_identifier(bagit_folder_preservica, "code", bagit_name)
            bagit_preserv_ref = bagit_folder_preservica.reference

            if collection.xip_package == "zip":
                # Preparing content for upload
                LOG.info(f"Creating metadata file for '{bagit_name}'")
                metadata_path = R2P.save_metadata(bagit_name)
                LOG.info(f"Creating zip with folder '{bagit_name}' content")
                zipfile = R2P.create_zipfile(bagit_dir)
                upload.upload_zip_package_to_S3(
                    path_to_zip_package=zipfile,
                    folder=bagit_preserv_ref,
                    bucket_name=collection.bucket,
                    callback=PRES.UploadProgressConsoleCallback(zipfile),
                    delete_after_upload=False,
                )
                LOG.info(f"Removing metadata file '{metadata_path}'")
                OS.remove(metadata_path)
                uploaded_folders.append(bagit_dir)

            elif collection.xip_package == "upload_api":
                LOG.info(f"Creating package for file in '{bagit_dir}'")
                package_path = R2P.create_package(bagit_dir, bagit_preserv_ref)
                LOG.info(f"Package path: '{package_path}'")

                LOG.info(f"Uploading {bagit_dir} to S3 bucket {collection.bucket}")
                upload.upload_zip_package_to_S3(
                    path_to_zip_package=package_path,
                    bucket_name=collection.bucket,
                    callback=PRES.UploadProgressConsoleCallback(package_path),
                    delete_after_upload=False,
                    folder=bagit_preserv_ref,
                )
            else:
                LOG.critical(
                    "'xip_package' must be 'zip' or 'upload_api'. Fix `ingest.cfg' file"
                )
                raise ValueError("Incorrect value for 'xip_package'")
            #
            # After the ingestion, give some time for Preservica to start
            # moving to our bucket.
            #
            LOG.info("Sleeping 2 minutes")
            TM.sleep(120)
            LOG.info("done")
            # Hopefully we don't need to control the number of ingested
            # files anymore
            # num_submissions = num_submissions + 1
        else:
            LOG.info(f"Preservica folder '{bagit_name}' already exists")
            LOG.info("Skipping folder")

    #
    # Compare SHA1 of files ingested with the original value from the
    # repository.
    #
    #
    # The End.
    #
    LOG.info("The End.")
    OS.chdir(old_dir)


@repo2pres.command()
@CL.option("-i", "--item", type=CL.STRING, help="Item to verify checksum")
@CL.option(
    "-l", "--file-list", type=CL.STRING, help="Input file with list of items to verify"
)
def verify(item: str, file_list: str) -> None:
    LOG.basicConfig(level=LOG.INFO)

    """Verify the checksum of ingested items"""
    DOT.load_dotenv()
    entity = PRES.EntityAPI()

    # We need to know the folder with
    input = "repo2preservica.cfg"
    collection = R2P.read_config(input)

    uploaded_folders = []

    if item:
        uploaded_folders.append(item)
    elif file_list:
        uploaded_folders = R2P.verify_flist(file_list)
    else:
        pass

    print(f"updated_folders: {uploaded_folders}")

    for uploaded in uploaded_folders:
        print(f"Bag name: '{uploaded}'")
        # We need to consider the time it takes for Preservica to scan the
        # new files for virus before making them available on our area.
        # We will wait for 10 minutes (5 times for 2 minutes). If not
        # enough, we gave up and abort the script.
        for cc in range(1, 6):
            pres_items_chk = R2P.pres_checksum(entity, uploaded)
            if pres_items_chk:
                LOG.info("Finished reading checksum from Preservica")
                break
            else:
                LOG.info(
                    "Waiting for Preservica scan items for virus and make them available for reading."
                )
                LOG.info(f"Sleeping 2 minutes, {cc} of 5.")
                TM.sleep(120)
        if not pres_items_chk:
            # Something went wrong!!
            LOG.critical(
                f"Unable to read items from Preservica after 5 attempts/10 minutes."
            )
            raise ValueError("'pres_items_chk' can't be empty after 10 minutes")
        r_uploaded_path = PL.Path.joinpath(
            PL.Path.cwd(), PL.Path(collection.data_folder), uploaded
        )
        repo_items_chk = R2P.repo_checksum(r_uploaded_path)
        for kk in repo_items_chk.keys():
            if repo_items_chk[kk] == pres_items_chk[kk]:
                LOG.info(f"{kk} is the same")
            elif repo_items_chk[kk] != pres_items_chk[kk]:
                LOG.warning(f"{kk} is mismatch")
            else:
                LOG.error("Error comparing checksum")


if __name__ == "__main__":
    # input = OS.path.join("config", "ingest.cfg")
    # print(f"Input file: {input}")

    repo2pres()
