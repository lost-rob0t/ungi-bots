#!/usr/bin/env python3

import csv
import json


def write_csv(file_name, headers, data_in):
    """
    Csv Writer used to dump data to csv
    """
    with open(file_name, "w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data_in)

def write_json(file_name, data):
    with open(file_name, "w") as json_file:
        for line in data:
            json_file.write(json.dumps(line) + "\n")
