CREATE TABLE ingested (
    id INTEGER PRIMARY KEY,
    id_item INTEGER NOT NULL,
    dt_ingest TEXT NOT NULL,
    is_verified INTEGER NOT NULL
);