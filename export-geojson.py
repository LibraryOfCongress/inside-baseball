#!/usr/bin/env python3

import re
import os
import sqlite3
import json
import sys


def export_items_as_geojson(db_file, output_file):
    db = sqlite3.connect("file:%s?mode=ro" % db_file, uri=True)
    db.row_factory = sqlite3.Row

    items = []

    for item in db.execute("SELECT * FROM Items LIMIT 100").fetchall():
        items.append(export_item_as_geojson(db, item))

    with open(output_file, "w") as output_f:
        json.dump({"type": "FeatureCollection", "features": items}, output_f)


MULTI_VALUE_COLUMN_RE = re.compile(r"^(.+)_\d+$")


def export_item_as_geojson(db, item):
    metadata = {}

    for k in item.keys():
        v = item[k]

        is_multi = MULTI_VALUE_COLUMN_RE.match(k)
        if not is_multi:
            metadata[k] = v
        else:
            base_key = is_multi.group(1)
            if base_key in metadata and not isinstance(metadata[base_key], list):
                existing_value = metadata.pop(base_key)
                metadata[base_key] = [existing_value]

            metadata[base_key].append(v)

    # Remove values which aren't worth having in the data:
    for k, v in metadata.items():
        if isinstance(v, list):
            metadata[k] = [i for i in v if i]

    # For our core fields we want to make sure we have a value even if they're
    # not consistent across all of our items:
    titles = [metadata.get("Object Name"), metadata.get("Title")]
    titles.extend(metadata.get("Other Title", []))

    display_titles = list(filter(None, titles))
    if not display_titles:
        title = metadata["Object Number"]
    else:
        title = display_titles[0]

    all_coords = []

    for lookup_name in (
        "Creator/Publisher",
        "Subject",
        "Era",
        "Geography",
        "Location",
        "Collection",
    ):
        db_ids = metadata[lookup_name]
        if not db_ids:
            continue
        if not isinstance(db_ids, list):
            db_ids = [db_ids]

        db_ids = ",".join(map(str, db_ids))

        if lookup_name == "Creator/Publisher":
            lookup_table = "Creator"
        else:
            lookup_table = lookup_name

        result = db.execute(f"SELECT * FROM {lookup_table} WHERE ROWID IN ({db_ids})")
        resolved_values = []

        for row in result.fetchall():
            resolved_values.append(row["value"])

            try:
                lat = row["latitude"]
                lng = row["longitude"]
            except IndexError:
                continue

            if lat and lng:
                all_coords.append((float(lng), float(lat)))

        metadata[lookup_name] = resolved_values

    if all_coords:
        coords = all_coords[0]
    else:
        coords = [0, 0]

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": coords},
        "properties": {"title": title, "metadata": metadata},
    }


if __name__ == "__main__":
    for f in sys.argv[1:]:
        output_filename = "%s.geojson" % os.path.splitext(f)[0]
        export_items_as_geojson(f, output_filename)
