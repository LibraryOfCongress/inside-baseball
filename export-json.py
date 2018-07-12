#!/usr/bin/env python3

import re
import os
import sqlite3
import json
import sys


def export_items_as_geojson(db_file, output_file):
    db = sqlite3.connect("file:%s?mode=ro" % db_file, uri=True)
    db.row_factory = sqlite3.Row

    all_points = {}
    all_items = {}

    for item in db.execute(
        "SELECT rowid, * FROM Items WHERE Items.'Object Type' != 'Web Page'"
    ).fetchall():
        points, item = export_item(db, item)

        item_id = item["id"]
        all_items[item_id] = item

        for point in points:
            combined_point = all_points.setdefault(
                point["latlng"], {"latlng": point["latlng"]}
            )
            combined_point.setdefault("items", set()).add(item_id)
            if not combined_point.get("title"):
                combined_point["title"] = point["title"]

    for point in all_points.values():
        # Sets are not serializable by the default JSON encoder
        point["items"] = list(point["items"])

    with open(output_file, "w") as output_f:
        json.dump({"points": list(all_points.values()), "items": all_items}, output_f)


MULTI_VALUE_COLUMN_RE = re.compile(r"^(.+)_\d+$")


def export_item(db, item):
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
        title = "Row #%d" % metadata["rowid"]
    else:
        title = display_titles[0]

    all_coords = dict()

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

        result = db.execute(f"SELECT * FROM {lookup_table} WHERE rowid IN ({db_ids})")
        resolved_values = []

        for row in result.fetchall():
            resolved_values.append(row["value"])

            try:
                lat = row["latitude"]
                lng = row["longitude"]
            except IndexError:
                continue

            if lat and lng:
                all_coords[(lat, lng)] = row["value"]

        metadata[lookup_name] = resolved_values

    return (
        [{"title": v, "latlng": k} for k, v in all_coords.items()],
        {"title": title, "metadata": metadata, "id": metadata["rowid"]},
    )


if __name__ == "__main__":
    for f in sys.argv[1:]:
        output_filename = "%s.json" % os.path.splitext(f)[0]
        export_items_as_geojson(f, output_filename)
