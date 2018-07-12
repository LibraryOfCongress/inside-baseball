#!/usr/bin/env python3

import csv
import sys


def clean_csv(input_file, output_file):
    csv_reader = csv.reader(input_file)
    csv_writer = csv.writer(output_file)

    for row in csv_reader:
        csv_writer.writerow(i.strip() for i in row)


if __name__ == "__main__":
    input_filename, output_filename = sys.argv[1:3]

    with open(input_filename, "r", encoding="utf-8") as input_file:
        with open(output_filename, "w", encoding="utf-8") as output_file:
            clean_csv(input_file, output_file)
