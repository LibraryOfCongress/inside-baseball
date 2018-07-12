all: server

clean:
	rm -f *.sqlite *.csv *-cleaned.xlsx

Final_Dataset-cleaned.xlsx: Final_Dataset.xlsx
	pipenv run python clean-xlsx.py Final_Dataset.xlsx

InsideBaseball.csv: Final_Dataset-cleaned.xlsx
	pipenv run in2csv Final_Dataset-cleaned.xlsx > InsideBaseball.csv

InsideBaseball.sqlite: Final_Dataset-cleaned.csv
	pipenv run python generate_sqlite_from_csv.py InsideBaseball.csv

geocode:
	pipenv run python geocode-locations.py InsideBaseball.sqlite

server: InsideBaseball.sqlite geocode
	pipenv run datasette serve InsideBaseball.sqlite
