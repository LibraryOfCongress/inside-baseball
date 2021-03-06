all: export

clean:
	rm -f *.sqlite *.csv *-cleaned.xlsx

InsideBaseball.csv: data/InsideBaseball-raw.csv
	pipenv run python clean-csv.py data/InsideBaseball-raw.csv InsideBaseball.csv

InsideBaseball.sqlite: InsideBaseball.csv
	pipenv run python generate_sqlite_from_csv.py InsideBaseball.csv

geocode: InsideBaseball.sqlite
	pipenv run python geocode-locations.py InsideBaseball.sqlite

InsideBaseball.json: geocode
	pipenv run python export-json.py InsideBaseball.sqlite

export: InsideBaseball.json

server: geocode
	pipenv run datasette serve InsideBaseball.sqlite

publish: geocode
	pipenv run datasette publish now --install=datasette-vega --install=datasette-cluster-map InsideBaseball.sqlite

upload: InsideBaseball.csv InsideBaseball.json InsideBaseball.sqlite
	cp InsideBaseball.csv InsideBaseball.json InsideBaseball.sqlite viewer/
	aws --profile=labs s3 sync --acl public-read --exclude=Makefile viewer/ s3://mappinganamericanpastime/
