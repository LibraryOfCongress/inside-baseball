#!/usr/bin/env python3

import json
import os
import sqlite3
import sys

import requests
from csvs_to_sqlite.utils import table_exists
from Levenshtein import ratio
from utils import column_exists, normalize_place_name

GEONAMES_API_USERNAME = os.environ.get("GEONAMES_API_USERNAME", "")

db = sqlite3.connect(sys.argv[1], isolation_level=None)

if not table_exists(db, "geonames_queries"):
    db.execute(
        """
        CREATE TABLE geonames_queries (
            id INTEGER PRIMARY KEY,
            value VARCHAR(255),
            fetched TIMESTAMP NULL,
            result_count INTEGER,
            geonames JSON NULL
        )
        """
    )

for table_name in ("Location", "Geography", "Subject"):
    if not column_exists(db, table_name, "latitude"):
        db.execute(f"ALTER TABLE {table_name} ADD COLUMN latitude VARCHAR(16) NULL")
        db.execute(f"ALTER TABLE {table_name} ADD COLUMN longitude VARCHAR(16) NULL")


# Look for new terms to search for:

source_queries = [
    """
    SELECT value FROM Geography WHERE value NOT IN (SELECT value FROM geonames_queries)
    """,
    """
    SELECT value FROM Location WHERE value NOT IN (SELECT value FROM geonames_queries)
    """,
    """
    SELECT value FROM Subject
        WHERE
            value NOT IN (SELECT value FROM geonames_queries)
            AND NOT value LIKE '%Team%'
    """,
]

for sql in source_queries:
    for (value,) in db.execute(sql).fetchall():
        query_value = normalize_place_name(value)

        db.execute(
            """
            INSERT INTO geonames_queries (value)
                SELECT ? WHERE NOT EXISTS (SELECT value FROM geonames_queries WHERE value = ?)
            """,
            (query_value, query_value),
        )

for (value,) in db.execute(
    "SELECT value FROM geonames_queries WHERE fetched IS NULL"
).fetchall():
    filters = {
        "username": GEONAMES_API_USERNAME,
        "maxRows": 10,
        "q": value,
        "country": "US",
    }

    r = requests.get("http://api.geonames.org/searchJSON", params=filters)
    r.raise_for_status()

    data = r.json()

    if data is None:
        print("Unable to decode JSON", file=sys.stderr)
        print(r.text_content, file=sys.stderr)
        continue

    result_count = int(data["totalResultsCount"])

    db.execute(
        """
            UPDATE geonames_queries
                SET fetched = CURRENT_TIMESTAMP,
                    result_count = ?,
                    geonames = ?
                WHERE value = ?;
        """,
        (result_count, json.dumps(data["geonames"]), value),
    )

    print(value, result_count, [i["name"] for i in data["geonames"]])


for table_name in ("Geography", "Location"):
    res = db.execute("SELECT value FROM %s" % table_name)
    for (value,) in res.fetchall():
        query_value = normalize_place_name(value)

        geonames_query = db.execute(
            "SELECT geonames FROM geonames_queries WHERE result_count > 0 AND value = ?",
            (query_value,),
        ).fetchone()

        if geonames_query:
            geonames = json.loads(geonames_query[0])
            lat = geonames[0]["lat"]
            lng = geonames[0]["lng"]

            db.execute(
                f"UPDATE {table_name} SET latitude = ?, longitude = ? WHERE value = ?",
                (lat, lng, value),
            )

# Subjects are messy and we might want to be careful about matches:
for (value,) in db.execute("SELECT value FROM Subject").fetchall():
    query_value = normalize_place_name(value)

    geoname_lookup = db.execute(
        "SELECT id, geonames FROM geonames_queries WHERE value = ?", (query_value,)
    ).fetchone()

    if not geoname_lookup:
        continue

    geoname_id, geonames = geoname_lookup

    geonames = json.loads(geonames)

    for geoname in geonames:
        name = geoname["name"] or geoname["toponymName"]
        match_ratio = ratio(value, name)

        if match_ratio > 0.8:
            lat = geoname["lat"]
            lng = geoname["lng"]
            db.execute(
                "UPDATE Subject SET latitude = ?, longitude = ? WHERE value = ?",
                (lat, lng, value),
            )
            break
    else:
        db.execute(
            "UPDATE Subject SET latitude = NULL, longitude = NULL WHERE value = ?",
            (value,),
        )


db.close()
