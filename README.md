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
-   The source metadata used in the app in the [`data` folder](./data/) and the
    processed data which the application uses:
    -   [`viewer/InsideBaseball.csv`](./viewer/InsideBaseball.csv)
    -   [`viewer/InsideBaseball.json`](./viewer/InsideBaseball.json)
    -   [`viewer/InsideBaseball.sqlite`](./viewer/InsideBaseball.sqlite)
    -   Team & player information in [`viewer/teams.geojson`](./viewer/teams.geojson)
-   Documentation and diagrams on data provenance, decisions, transformations in
    [`data/original`](./data/original/)
-   [Data Wireframe](./data/original/Inside Baseball Wireframe.pptx)
