import csv


def read_from_csv(in_filepath):
    rows = []
    with open(in_filepath, "r") as in_file:
        dict_reader = csv.DictReader(in_file, skipinitialspace=True)
        rows = [{k: v for k, v in row.items()} for row in dict_reader]
    return rows


def write_to_csv(rows, out_filepath):
    with open(out_filepath, 'w') as out_file:
        writer = csv.DictWriter(out_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
