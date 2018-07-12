all: export

clean:
	rm -f *.sqlite *.csv *-cleaned.xlsx

Final_Dataset-cleaned.xlsx: Final_Dataset.xlsx
	pipenv run python clean-xlsx.py Final_Dataset.xlsx

Final_Dataset-cleaned.csv: Final_Dataset-cleaned.xlsx
	pipenv run in2csv Final_Dataset-cleaned.xlsx > Final_Dataset-cleaned.csv

InsideBaseball.csv: InsideBaseball-raw.csv
	pipenv run python clean-csv.py InsideBaseball-raw.csv InsideBaseball.csv

InsideBaseball.sqlite: InsideBaseball.csv
	pipenv run python generate_sqlite_from_csv.py InsideBaseball.csv

geocode: InsideBaseball.sqlite
	pipenv run python geocode-locations.py InsideBaseball.sqlite

export: geocode
	pipenv run python export-json.py InsideBaseball.sqlite
	mv InsideBaseball.json viewer/

server: geocode
	pipenv run datasette serve InsideBaseball.sqlite

publish: geocode
	pipenv run datasette publish now --install=datasette-vega --install=datasette-cluster-map InsideBaseball.sqlite
