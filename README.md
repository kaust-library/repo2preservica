# Repo to Preservica

Script to ingest files from the institutional repository into Presevica.

Structural objects define the organisation of the data. In a library context they may be referred to as collections, in an archival context they may be Fonds, Sub-Fonds, Series etc and in a records management context they could be simply a hierarchy of folders or directories.

These structural objects may contain other structural objects in the same way as a computer filesystem may contain folders within folders.

Within the structural objects comes the information objects. These objects which are sometimes referred to as the digital assets are what PREMIS defines as an Intellectual Entity. Information objects are considered a single intellectual unit for purposes of management and description: for example, a book, document, map, photograph or database etc.

request an Asset (Information Object) by its unique reference and display some of its attributes. Information objects are considered a single intellectual unit for purposes of management and description: for example, a book, document, map, photograph or database etc.

## Configuration

Files that need to be edited before running the script:

- `.env` with the credentials to Preservica. See the file `.env_example`
- `etc/repo2preservica.cfg` with informations "run time" information like the directory with the subdirectories to ingest, which Preservica folder to use, among others.

## Initializing the Database

Before the first run of the script, it's necessary to initialize the database by running the script `createdb.py.` The script will read the three SQL files and create the tables.

```
(r2p) PS C:\Users\garcm0b\Work\repo2preservica\db_helper> python .\createdb.py
Creating table from 'items.sql'... done
Creating table from 'verify.sql'... done
Creating table from 'ingest.sql'... done
```

And this will create the db file in the parent directory

```
(r2p) PS C:\Users\garcm0b\Work\repo2preservica> ls
(...)
-a---            9/5/2023  2:18 PM          16384 r2p.db
```

## Command Line Options

The general configuration is located in the `etc` directory, but details can be customized with some command line options:

- Options to the `ingest` script:

  - `-i | --input-folder`: specify the folder with the items to ingest.
  - `-p | --parent-folder`: The parent folder in Preservica.

```
(r2p) PS C:\Users\garcm0b\Work\repo2preservica> python .\src\ingest.py --help
Usage: ingest.py [OPTIONS]

  Ingest items from repository into Preservica

Options:
  -i, --input-folder TEXT   Folder with the items to ingest
  -p, --parent-folder TEXT  Preservica parent folder
  --help                    Show this message and exit.
(r2p) PS C:\Users\garcm0b\Work\repo2preservica>
```

- Options to the `verify` parameter:

  - `-i | --item`: the item to verify.
  - `-l | --list 'filename'`: file with a list of items to verify.

- Options for the `history` parameter:
  - `-a | --all`: list all ingested items.
  - `-s | --start-date YYYY-MM-DD`: list ingestion starting from `start-date`.
  - `-l | --list 'filename'`: file with list of items to verify.

## Database

The history of ingestion and verification is stored in a SQLite database:

```
Tables:

item | ingested | verified |
-----+----------+----------+
id   | id       | id       |
item | date     | date     |
     | item_id  | item_id  |



Example of all records:

item | ingested   | verified   |
-----+------------+------------+
xyz  | YYYY-MM-DD | YYYY-MM-DD |
abc  | YYYY-MM-DD | YYYY-MM-DD |
abc  | YYYY-MM-DD | YYYY-MM-DD |
abc  | YYYY-MM-DD | YYYY-MM-DD |
def  | YYYY-MM-DD | YYYY-MM-DD |

```

## Running the Script

The script will try to import all folders in `data_folder` defined in the `ingest.cfg` file (`config` folder). It will say how many folders it was found, and the log messages will inform of the progress, like uploading or skipping because the folder already exists in Preservica.

```
(venv) PS C:\Users\garcm0b\Work\repo2preservica> python .\src\repo2preservica.py .\config\ingest.cfg
(venv) PS C:\Users\garcm0b\Work\repo2preservica> python .\src\repo2preservica.py .\config\ingest.cfg
INFO:root:Entity: 'pyPreservica version: 1.6.1  (Preservica 6.5 Compatible) Connected to: eu.preservica.com Preservica version: 6.6.1 as eamon.smallwood@kaust.edu.sa in tenancy KAUST'
INFO:root:Files will be ingest into 'REPOSITORY_ETD_TEST'.
INFO:root:Start of bagging process.
INFO:root:We found 16 folders to scan
INFO:root:Creating Preservica folder '10754_136193'
INFO:root:Creating metadata file for '10754_136193'
INFO:root:Creating zip with folder '10754_136193' content
INFO:root:Removing metadata file '10754_136193\10754_136193.metadata'██████████████████████████████████████████| (100.00%) (0.61 Mb/s)
INFO:root:Preservica folder '10754_136194' already exists
INFO:root:Skipping folder
INFO:root:Creating Preservica folder '10754_136195'
(...)
```

After the ingestion, the next step is to verify if the files are the same. The test is to compare the checksum from the Repository with the one generated by Preservica during the ingestion:

```
Bag name: '10754_136193'
INFO:root:Finished reading checksum from Preservica
INFO:root:10754_136193.json is the same
INFO:root:10754_136193.xml is the same
INFO:root:147584-295966.json is the same
INFO:root:147584-295967.json is the same
INFO:root:147584-295967.pdf is the same
INFO:root:147584-295968.json is the same
INFO:root:147584-295968.pdf is the same
INFO:root:sha256.txt is the same
INFO:root:data/147584-295966.metadata is the same
INFO:root:data/147584-295966.pdf is the same
```

When setting the ownership of the directory to `library-sds`, it's necessary to "inform" git about it:

```
(venv) a-garcm0b@lthlibtest:/data/scripts$ sudo chown -R library-sds:ci-library repo2preservica/
(venv) a-garcm0b@lthlibtest:/data/scripts/repo2preservica$ git pull
fatal: detected dubious ownership in repository at '/data/scripts/repo2preservica'
To add an exception for this directory, call:

        git config --global --add safe.directory /data/scripts/repo2preservica
(venv) a-garcm0b@lthlibtest:/data/scripts/repo2preservica$
(venv) a-garcm0b@lthlibtest:/data/scripts/repo2preservica$ git config --global --add safe.directory /data/scripts/repo2preservica
(venv) a-garcm0b@lthlibtest:/data/scripts/repo2preservica$ sudo -i -u library-sds
library-sds@lthlibtest:/data/scripts/repo2preservica$ whoami
library-sds
library-sds@lthlibtest:/data/scripts/repo2preservica$
library-sds@lthlibtest:/data/scripts/repo2preservica$ git pull
Already up to date.
library-sds@lthlibtest:/data/scripts/repo2preservica$
```

## Pywin32 and Linux

When installing on Linux, the `pip install` will fail because the package `pywin32` is missing. The [workaround is to add a parameter](https://github.com/mhammond/pywin32/issues/1739) to the entry of the package in the `requirements.txt` marking as Windows only package

```
pywin32==305; platform_system=="Windows"
```

When installing on Linux, you will see message about ignoring the package

```
(venv) mgarcia@PC-KL-21621:~/Work/repo2preservica$ pip install -r requirements.txt
Ignoring pywin32: markers 'platform_system == "Windows"' don't match your environment
(...)
```
