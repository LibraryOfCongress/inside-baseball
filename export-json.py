#!/usr/bin/env python3

import json
import os
import re
import sqlite3
import sys

import dateparser


def load_image_json():
    with open("images.json", "r") as f:
        data = json.load(f)

    images = {}

    for image in data:
        item_url = image.get("itemURL")
        thumbnail = image.get("imageThumb")
        large = image.get("imageLarge")

        if not item_url:
            print("Malformed row:", image, file=sys.stderr)
            continue

        if thumbnail == "&max=100":
            thumbnail = ""

        if not thumbnail and not large:
            print(f"No images for {item_url}!", image, file=sys.stderr)
            continue
        elif not thumbnail and large:
            thumbnail = large
        elif not large and thumbnail:
            large = thumbnail

        images[item_url] = {"imageThumbnail": thumbnail, "imageLarge": large}

    return images


IMAGE_JSON = load_image_json()


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
        json.dump({"points": list(all_points.values()), "items": all_items}, output_f, indent=4)


MULTI_VALUE_COLUMN_RE = re.compile(r"^(.+)[._]\d+$")


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

    all_coords = dict()

    for lookup_name in (
        "Other Title",
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
        elif lookup_name == "Other Title":
            lookup_table = "Title"
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

    # For our core fields we want to make sure we have a value even if they're
    # not consistent across all of our items:
    titles = [metadata.get("Object Name"), metadata.get("Title")]
    titles.extend(filter(None, metadata["Other Title"] or []))

    display_titles = list(filter(None, titles))
    if not display_titles:
        title = "Row #%d" % metadata["rowid"]
    else:
        title = display_titles[0]

    item_properties = {
        "title": title,
        "metadata": metadata,
        "id": str(metadata.pop("rowid")),
    }

    item_url = metadata["Digital ID URL"]
    if item_url not in IMAGE_JSON:
        print("No images for item", item_url, file=sys.stderr)
    else:
        item_properties.update(IMAGE_JSON[item_url])

    extracted_dates = extract_dates(metadata.get("Date"))
    if extracted_dates:
        item_properties["startYear"] = int(extracted_dates[0])
        item_properties["endYear"] = int(extracted_dates[1])

    return ([{"title": v, "latlng": k} for k, v in all_coords.items()], item_properties)


def extract_dates(raw_input):
    if not raw_input:
        return

    d = raw_input.strip()

    d = re.sub(r"^(?:ca?.|early)\s*", "", d)
    d = re.sub(r"(; (printed|used|scanned) .*$)", "", d)

    if re.match(r'^"?\w+\s+(|\d+,\s+)\d{4}"?$', d):
        date = dateparser.parse(d, languages=["en"])
        if date:
            return date.year, date.year

    start_year = end_year = None

    if "-" not in d:
        guess = guess_years_from_date_string(d)
        if guess:
            start_year, end_year = guess
    else:
        chunks = re.split("\s*-\s*", d, maxsplit=1)

        for guess in map(guess_years_from_date_string, chunks):
            if not guess:
                continue

            if guess[0] and (not start_year or start_year > guess[0]):
                start_year = guess[0]

            if guess[1] and (not end_year or end_year < guess[1]):
                end_year = guess[1]

    if not start_year:
        m = re.search(r"(\d{4})", d)
        if m:
            start_year = m.group(1)

    if not start_year:
        print(f"Unable to parse a date from {raw_input}", file=sys.stderr)

    if not end_year:
        end_year = start_year

    return start_year, end_year


DATE_RE = re.compile(r"^(\d{4})$")
DATE_RANGE_RE = re.compile(r"^(\d{4})-(\d{4})$")
DECADE_RE = re.compile(r"^(\d{4})s$")


def guess_years_from_date_string(d):
    m = DATE_RE.match(d)
    if m:
        return m.group(1), m.group(1)

    m = DATE_RANGE_RE.match(d)
    if m:
        return m.group(1), m.group(2)

    m = DECADE_RE.match(d)
    if m:
        return m.group(1), "%s9" % m.group(1)[0:3]


if __name__ == "__main__":
    for f in sys.argv[1:]:
        output_filename = "%s.json" % os.path.splitext(f)[0]
        export_items_as_geojson(f, output_filename)
