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
import datetime as DT


@CL.command()
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
        uploaded_folders = R2P.db_unverified()

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


def main():
    verify()


if __name__ == "__main__":
    # input = OS.path.join("config", "ingest.cfg")
    # print(f"Input file: {input}")

    main()
