# Inside Baseball: Baseball Collections as Data Event Background

LC Labs, JSTOR Labs, and the National Museum of African American History and
Culture collaborated on Inside Baseball Week (7/9/2018-7/13/2018), an exercise
in user-centered design rapid-prototyping to create applications to access
baseball digital collections across our cultural heritage organizations.

LC Labs built the application
[“Mapping an American Pastime”](https://labs.loc.gov/experiments/mapping-an-american-pastime/)
which uses a timeline, mapping, and free-text search to browse baseball-related
digital collections from the Library of Congress and the National Museum of
African American History and Culture. JSTOR Labs facilitated the LC Labs team in
their first data-jam and flash build effort.

The LC Labs team and the JSTOR Labs team publicly presented their applications
at the Inside Baseball Labs Showcase on Friday, July 13th, 2018. The archived
livestream of the event is [here](https://youtu.be/OUZynlvsQSo?t=3m50s).

We’d like to thank first and foremost our data divinator, visiting Archivist
Julia Hickey, our Library of Congress team members Griff Friedman, UX Designer,
Chris Adams, LC Information Technology Specialist, Meghan Ferriter, Abbey
Potter, and Jaime Mears of LC Labs, and our amazing support crew: Junior Fellows
Eileen Jakeaway and Courtney Johnson, HACU Intern Yassira Sueiras, and UVA
Fellow Erin Dlott.

We’d also like to thank our fearless leader, JSTOR Labs facilitator Beth
Dufford.

## Repo Content

You will find the following in this repo:

-   [“Mapping an American Pastime” application](https://labs.loc.gov/experiments/mapping-an-american-pastime/)
    source code in the [`viewer/`](./viewer/) folder
-   The source metadata used in the app in the [`data` folder](./data/) and the
    processed data which the application uses:
    -   [`viewer/InsideBaseball.csv`](./viewer/InsideBaseball.csv)
    -   [`viewer/InsideBaseball.json`](./viewer/InsideBaseball.json)
    -   [`viewer/InsideBaseball.sqlite`](./viewer/InsideBaseball.sqlite)
    -   Team & player information in [`viewer/teams.geojson`](./viewer/teams.geojson)
-   The code used to process the data step by step in the provided Makefile (see
    “Processing the Data” below)
-   Documentation and diagrams on data provenance, decisions, transformations in
    [`data/original`](./data/original/)
-   [Data Wireframe](./data/original/Inside Baseball Wireframe.pptx)

## Processing the Data

The raw data is processed using a Python 3.7-based pipeline. For consistent
installation, the Python dependencies are managed using
[pipenv](https://docs.pipenv.org/) — simply run `pipenv install` and you should
be able to run each utility described below.

GNU Make is used to batch all of these operations together so you can simply
type `make` and run each step in sequence.

### Converting the CSV

The [`clean-csv.py`](./clean-csv.py) utility takes the raw CSV data and
generates a version which has any leading or trailing space removed and
implicitly ensures that the data is valid Unicode encoded using UTF-8:

    pipenv run python clean-csv.py data/InsideBaseball-raw.csv InsideBaseball.csv

The [`generate_sqlite_from_csv.py`](./generate_sqlite_from_csv.py) utility
creates the SQLite database from the CSV file. This allows complex queries using
tools such as [Datasette](https://github.com/simonw/datasette) and simplifies
the process of iteratively running data modification queries, such as the
geocoding process:

    pipenv run python generate_sqlite_from_csv.py InsideBaseball.csv

### Geocoding

The geocoder uses GeoNames.org to attempt to find places for the named locations
and subjects. This is not perfect (e.g. “Salisbury” matched Salisbury MD rather
than the intended Salisbury NC) but is a convenient starting point:

    pipenv run python geocode-locations.py InsideBaseball.sqlite

At this point you can view the SQLite database locally using Datasette:

    pipenv run datasette serve InsideBaseball.sqlite

Since we had the
[datasette-cluster-map](https://pypi.org/project/datasette-cluster-map/) plugin
installed this allowed the entire team to look at the geocoding results and
report errors.

### Running the viewer

Finally, we used the `export-json.py` utility to generate the data file used by
the viewer from the processed data in SQLite:

    pipenv run python export-json.py InsideBaseball.sqlite

This does not use GeoJSON because we wanted to avoid having more than one pin on
the map for a given location, which meant that the pins map to the referenced
locations rather than specific items and since items may reference many points
we wanted to avoid duplicating the full item record for each location.
