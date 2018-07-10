#!/usr/bin/env python3

import json
import re
import os
import sqlite3
import sys

import requests
from csvs_to_sqlite.utils import table_exists

from utils import column_exists, normalize_place_name

GEONAMES_API_USERNAME = os.environ.get("GEONAMES_API_USERNAME", "acdha")

db = sqlite3.connect(sys.argv[1], isolation_level=None)

if not table_exists(db, "geonames"):
    db.execute(
        """
        CREATE TABLE geonames (
            id INTEGER PRIMARY KEY,
            value VARCHAR(255),
            fetched TIMESTAMP NULL,
            result_count INTEGER,
            geonames JSON NULL,
            latitude VARCHAR(16) NULL,
            longitude VARCHAR(16) NULL
        )
        """
    )

for table_name in ("Location", "Geography", "Subject"):
    if not column_exists(db, table_name, "geoname"):
        db.execute(
            f"ALTER TABLE {table_name} ADD COLUMN geoname INTEGER NULL REFERENCES geonames (id)"
        )


# Look for new terms to search for:

source_queries = [
    """
    SELECT value FROM Geography WHERE value NOT IN (SELECT value FROM geonames)
    """,
    """
    SELECT value FROM Location WHERE value NOT IN (SELECT value FROM geonames)
    """,
    """
    SELECT value FROM Subject
        WHERE
            value NOT IN (SELECT value FROM geonames)
            AND NOT value LIKE '%Team%'
    """,
]

for sql in source_queries:
    for (value,) in db.execute(sql).fetchall():
        query_value = normalize_place_name(value)

        db.execute(
            """
            INSERT INTO geonames (value)
                SELECT ? WHERE NOT EXISTS (SELECT value FROM geonames WHERE value = ?)
            """,
            (query_value, query_value),
        )

for (value,) in db.execute(
    "SELECT value FROM geonames WHERE fetched IS NULL"
).fetchall():
    filters = {
        "username": GEONAMES_API_USERNAME,
        "maxRows": "3",
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

    if result_count:
        first_result = data["geonames"][0]
        lat = first_result["lat"]
        lng = first_result["lng"]
        geonameId = first_result["geonameId"]
    else:
        lat = lng = geonameId = ""

    db.execute(
        """
            UPDATE geonames
                SET fetched = CURRENT_TIMESTAMP,
                    result_count = ?,
                    geonames = ?,
                    latitude = ?,
                    longitude = ?
                WHERE value = ?;
        """,
        (result_count, json.dumps(data["geonames"]), lat, lng, value),
    )

    print(value, result_count, geonameId, lat, lng)

for table_name in ("Geography", "Location", "Subject"):
    res = db.execute("SELECT value FROM %s WHERE geoname IS NULL" % table_name)
    for (value,) in res.fetchall():
        query_value = normalize_place_name(value)
        db.execute(
            f"UPDATE {table_name} SET geoname = (SELECT id FROM geonames WHERE value = ?) WHERE value = ?",
            (query_value, value),
        )

db.close()
