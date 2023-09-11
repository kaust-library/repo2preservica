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
        pres_items_chk = R2P.pres_checksum(entity, uploaded)
        if not pres_items_chk:
            # Something went wrong!!
            raise ValueError("'pres_items_chk' can't be empty")
        r_uploaded_path = PL.Path.joinpath(
            PL.Path.cwd(), PL.Path(collection.data_folder), uploaded
        )
        repo_items_chk = R2P.repo_checksum(r_uploaded_path)
        for kk in repo_items_chk.keys():
            if repo_items_chk[kk] == pres_items_chk[kk]:
                LOG.info(f"{kk} is the same")
                chk_status = 1
            elif repo_items_chk[kk] != pres_items_chk[kk]:
                LOG.warning(f"{kk} is mismatch")
                chk_status = 2                
            else:
                LOG.error("Error comparing checksum")
                chk_status = 3                
    

def main():
    verify()


if __name__ == "__main__":
    # input = OS.path.join("config", "ingest.cfg")
    # print(f"Input file: {input}")

    main()
