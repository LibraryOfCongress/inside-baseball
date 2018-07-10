#!/usr/bin/env python3

import os
import sys

from openpyxl import load_workbook

for xlsx in sys.argv[1:]:
    wb = load_workbook(filename=xlsx)

    for worksheet in wb.worksheets:
        for row in worksheet.rows:
            for cell in row:
                if cell.data_type in ("s",):
                    cell.value = cell.value.strip()

    wb.save(filename="%s-cleaned%s" % os.path.splitext(xlsx))
