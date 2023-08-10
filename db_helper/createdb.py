#
# Create the database and tables from the SQL files.

import sqlite3
from pathlib import Path

def read_sql(sql_file):
    """
    Read the content of a SQL file.
    """
    with open(sql_file,'r') as ff:
        text = ff.readlines()

    # Convert list to text
    command = ''.join([line.strip() for line in text])
    return command


def main():
    sql_tables = ['items.sql', 'verify.sql', 'ingest.sql']
    #
    # Put the db in parent folder of "db_helper" (the current folder (cwd)).
    sql_dir = Path.cwd().parent
    sql_file = sql_dir / 'r2p.db'

    con = sqlite3.connect(sql_file)

    cur = con.cursor()

    for tt in sql_tables:
        print(f"Creating table from '{tt}'", end='... ')
        command = read_sql(tt)
        cur.execute(command)
        print('done')


if __name__ == "__main__":
    main()