import click as CL
from pathlib import Path
from sqlite3 import connect


def query_unverified(conn):

    with conn:
        res = conn.execute(
            """
            SELECT item, dt_ingest FROM items 
            INNER JOIN ingested on items.id = ingested.id_item;
    """)
        
    for rr in res:
        print(rr)

def main():
    db_file = Path(".").parent.joinpath("r2p.db")

    if db_file.exists():
        conn = connect(db_file)
    else:
        raise FileNotFoundError

    query_unverified(conn)

    #
    # The End.
    print("Have a nice day.")


if __name__ == "__main__":
    main()
