import re


def get_table_columns(db, table_name):
    return db.execute("PRAGMA table_info(%s)" % table_name).fetchall()


def column_exists(db, table_name, column_name):
    for row in get_table_columns(db, table_name):
        if row[1] == column_name:
            return True

    return False


def normalize_place_name(value):
    """Quick and dirty conversion of common verbiage around placenames"""
    query_value = value
    query_value = re.sub(r"^Place \w+:", "", query_value)
    query_value = re.sub(r"^Cultural Place:", "", query_value)
    query_value = query_value.strip()

    return query_value
