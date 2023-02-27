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

@CL.command()
@CL.argument("input", type=CL.Path("r"))
def main(input):

    LOG.basicConfig(encoding="utf-8", level=LOG.INFO)

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
    collection = R2P.read_config(input)

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
    skipped_folder = ""
    for bagit_dir in bagit_dirs:
        # Remove the folders that were skipped, and keep only the ones that
        # were uploaded
        if skipped_folder:
            bagit_dirs.remove(skipped_folder)
            skipped_folder = ""

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
        else:
            LOG.info(f"Preservica folder '{bagit_name}' already exists")
            LOG.info("Skipping folder")
            skipped_folder = bagit_dir

    #
    # Compare SHA1 of files ingested with the original value from the
    # repository.
    #
    # for dir in bagit_dirs:
    #     sha1_repo = R2P.load_sha_repo(dir)
    #     PP.pprint(sha1_repo)

    #
    # The End.
    #
    LOG.info("The End.")
    OS.chdir(old_dir)


if __name__ == "__main__":

    # input = OS.path.join("config", "ingest.cfg")
    # print(f"Input file: {input}")

    main()
