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

# Media

-   [Inside, Inside Baseball: A Look at the Construction of the Dataset Featuring the Smithsonian’s National Museum of African American History and Culture and the Library of Congress Digital Collections](https://blogs.loc.gov/thesignal/2018/07/inside-inside-baseball-a-look-at-the-construction-of-the-dataset-featuring-the-smithsonians-national-museum-of-african-american-history-and-culture-and-the-library-of-congress-digital-collect/)
-   Livestream archive: [Inside Baseball: Baseball Collections as Data](https://www.youtube.com/watch?v=OUZynlvsQSo)

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
type `make` to run each step described below in sequence.

### Converting the CSV (`make InsideBaseball.csv`)

The [`clean-csv.py`](./clean-csv.py) utility takes the raw CSV data and
generates a version which has any leading or trailing space removed and
implicitly ensures that the data is valid Unicode encoded using UTF-8:

```bash
$ pipenv run python clean-csv.py data/InsideBaseball-raw.csv InsideBaseball.csv
```

### Generate a SQLite database from the CSV (`make InsideBaseball.sqlite`)

The [`generate_sqlite_from_csv.py`](./generate_sqlite_from_csv.py) utility
creates the SQLite database from the CSV file. This allows complex queries using
tools such as [Datasette](https://github.com/simonw/datasette) and simplifies
the process of iteratively running data modification queries, such as the
geocoding process:

```bash
$ pipenv run python generate_sqlite_from_csv.py InsideBaseball.csv
```

### Geocoding (`make geocode`)

The geocoder uses GeoNames.org to attempt to find places for the named locations
and subjects. This is not perfect (e.g. “Salisbury” matched Salisbury MD rather
than the intended Salisbury NC) but is a convenient starting point:

```bash
$ pipenv run python geocode-locations.py InsideBaseball.sqlite
```

n.b. you will need to define the `GEONAMES_API_USERNAME` environmental variable
in your shell before running that command after registering, as per the
instructions on https://www.geonames.org/export/web-services.html.

### Viewing the results using Datasette (`make server`)

At this point you can view the SQLite database locally using Datasette:

```bash
$ pipenv run datasette serve InsideBaseball.sqlite
```

Since we had installed the
[datasette-cluster-map](https://pypi.org/project/datasette-cluster-map/) plugin
the entire team was able to look at the geocoding results and report errors at
this stage while the viewer was under active development.

### Exporting JSON for the viewer (`make export`)

Finally, we used the `export-json.py` utility to generate the data file used by
the viewer from the processed data in SQLite:

```bash
$ pipenv run python export-json.py InsideBaseball.sqlite
```

This does not use GeoJSON because we wanted to avoid having more than one pin on
the map for a given location, which meant that the pins map to the referenced
locations rather than specific items and since items may reference many points
we wanted to avoid duplicating the full item record for each location.

### Running the viewer

At this point all of the data is ready for the viewer. Opening
`viewer/index.html` may work depending on your browser and configuration but
heightened security policies may require running everything through a webserver.
You can copy the contents of the `viewer` directory to the server of your choice
or run a simple local server for testing:

```bash
$ pipenv run python -m http.server --directory viewer
```
