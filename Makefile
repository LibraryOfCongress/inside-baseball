all: Final_Dataset-cleaned.sqlite

clean:
	rm -f *.sqlite *.csv *-cleaned.xlsx

Final_Dataset-cleaned.xlsx: Final_Dataset.xlsx
	pipenv run python clean-xlsx.py Final_Dataset.xlsx

Final_Dataset-cleaned.csv: Final_Dataset-cleaned.xlsx
	pipenv run in2csv Final_Dataset-cleaned.xlsx > Final_Dataset-cleaned.csv

Final_Dataset-cleaned.sqlite: Final_Dataset-cleaned.csv
	pipenv run python generate_sqlite_from_csv.py Final_Dataset-cleaned.csv Final_Dataset-cleaned.sqlite
