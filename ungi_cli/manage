#!/usr/bin/env python3

import argparse
import json
import cmd2
from utils.Elastic_Wrapper import search
from  utils.Sqlite3_Utils import create_operation, list_ops, add_subreddit
import functools
import sys
from typing import (
    Any,
    List,
)

from cmd2 import (
    ansi,
)
from cmd2.table_creator import (
    AlternatingTable,
    BorderedTable,
    Column,
    HorizontalAlignment,
    SimpleTable,
)
def ansi_print(text):
    ansi.style_aware_write(sys.stdout, text + '\n\n')

class OperationsManager(cmd2.Cmd):
    def __init__(self):
        super().__init__()

        self.database_path = "app.ini"
        self.elastic_host = "http://127.0.0.1:9200"
        self.prompt = "Ungi[manage]> "
        self.add_settable(cmd2.Settable("database_path", str, "path to ungi database"))
    operations_parser = argparse.ArgumentParser()
    operations_parser.add_argument("-c", "--create")
    operations_parser.add_argument("-d", "--desc", help="Description for the Operation")
    operations_parser.add_argument("-r", "--remove", help="remove an Operation with all data and loot associated with it")
    @cmd2.with_argparser(operations_parser)
    def do_create(self, args):
        print(f"Creating operation: {args.create}")
        create_operation(self.database_path, args.create, args.desc)

    def do_list_ops(self, *args):
        columns: List[Column] = list()
        columns.append(Column("ID", width=12))
        columns.append(Column("Name", width=20))
        columns.append(Column("Description", width=30,
                              header_horiz_align=HorizontalAlignment.RIGHT,
                              data_horiz_align=HorizontalAlignment.CENTER))

        ops = list_ops(self.database_path)
        data_list: List[List[Any]] = list()
        for op in ops:
           data_list.append([op[0], op[1], op[2]])

        bt = BorderedTable(columns)
        table = bt.generate_table(data_list)
        ansi_print(table)


if __name__ == '__main__':
    import sys
    ops = OperationsManager()
    sys.exit(ops.cmdloop())
