# Repo to Preservica

Script to ingest files from the institutional repository into Presevica.

Structural objects define the organisation of the data. In a library context they may be referred to as collections, in an archival context they may be Fonds, Sub-Fonds, Series etc and in a records management context they could be simply a hierarchy of folders or directories.

These structural objects may contain other structural objects in the same way as a computer filesystem may contain folders within folders.

Within the structural objects comes the information objects. These objects which are sometimes referred to as the digital assets are what PREMIS defines as an Intellectual Entity. Information objects are considered a single intellectual unit for purposes of management and description: for example, a book, document, map, photograph or database etc.

request an Asset (Information Object) by its unique reference and display some of its attributes. Information objects are considered a single intellectual unit for purposes of management and description: for example, a book, document, map, photograph or database etc.

## Configuration

Use the file `.env_example` to customize your version of the `.env` file with the credentials for Preservica.

## Running the Script

The script will try to import all folders in `data_folder` defined in the `ingest.cfg` file (`config` folder).
