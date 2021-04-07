#!/usr/bin/env python3

import argparse
import json
import cmd2
from  utils.Sqlite3_Utils import (
    create_operation,
    list_ops,
    add_subreddit,
    get_op_id,
    add_discord,
)
from utils.Config import config
from os import environ
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

        try:
            self.config_path = environ["UNGI_CONFIG"]
            self.database_path = config("DB", "path", environ["UNGI_CONFIG"])
        except KeyError as no_value:
            self.config_path = input("Please input the path to config file")
            self.database_path = config("DB", "path", self.config_path)
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

    reddit_bulk_parser = argparse.ArgumentParser()
    reddit_bulk_parser.add_argument("-i", "--input", help="File with list of subreddits")
    reddit_bulk_parser.add_argument("-n", "--name", help="name of operation")
    reddit_bulk_parser.add_argument("--id", help="operation id")
    @cmd2.with_argparser(reddit_bulk_parser)
    def do_reddit_bulk(self, args):
        columns: List[Column] = list()
        columns.append(Column("ID", width=12))
        columns.append(Column("Subreddit", width=30,
                              header_horiz_align=HorizontalAlignment.CENTER, data_horiz_align=HorizontalAlignment.CENTER))
        reddit_list: List[List[Any]] = list()
        subreddits = []
        if args.name:
            op_id = get_op_id(self.database_path, args.name)[0]
        else:
            op_id = int(args.id)
        sub_id = 1
        with open(args.input, "r") as reddit_file:
            for line in reddit_file:
                reddit_list.append([sub_id, line])
                subreddits.append(line)
                sub_id += 1

        bt = BorderedTable(columns)
        table = bt.generate_table(reddit_list)
        ansi_print(table)
        choice = input("Is this ok? (y/n) ")
        if choice == "y":
            for sub in subreddits:
                add_subreddit(self.database_path, sub, int(op_id[0]))
        else:
            print("Canceled")

    discord_bulk = argparse.ArgumentParser()
    discord_bulk.add_argument("-i", "--input", help="file containing discord id's")
    discord_bulk.add_argument("-id", help="operation id")
    discord_bulk.add_argument("-n", "--name", help="operation_name")
    @cmd2.with_argparser(discord_bulk)
    def do_discord_bulk(self, args):
        columns: List[Column] = list()
        columns.append(Column("ID", width=12))
        columns.append(Column("Server ID", width=30,
                              header_horiz_align=HorizontalAlignment.CENTER, data_horiz_align=HorizontalAlignment.CENTER))
        reddit_list: List[List[Any]] = list()
        subreddits = []
        if args.name:
            op_id = get_op_id(self.database_path, args.name)[0]
        else:
            op_id = int(args.id)
        sub_id = 1
        with open(args.input, "r") as reddit_file:
            for line in reddit_file:
                reddit_list.append([sub_id, line])
                subreddits.append(line)
                sub_id += 1

        bt = BorderedTable(columns)
        table = bt.generate_table(reddit_list)
        ansi_print(table)
        choice = input("Is this ok? (y/n) ")
        if choice == "y":
            for sub in subreddits:
                add_discord(self.database_path, sub, int(op_id[0]))
        else:
            print("Canceled")

    add_parser = argparse.ArgumentParser()
    add_parser.add_argument("-d", help="Discord", action="store_true")
    add_parser.add_argument("-r", help="Reddit", action="store_true")
    add_parser.add_argument("-Id", help="Operation id")
    add_parser.add_argument("-i", help="input")
    @cmd2.with_argparser(add_parser)
    def do_add(self, args):
        if args.d:
            print(f"adding {args.i}")
            choice = input("is this ok? (y/n): ")
            if choice == "y":
                add_discord(self.database_path, args.i, args.Id)
            else:
                print("Canceled")

        if args.r:
            print(f"adding {args.i}")
            choice = input("is this ok? (y/n): ")
            if choice == "y":
                add_subreddit(self.database_path, args.i, args.Id)
            else:
                print("Canceled")
if __name__ == '__main__':
    import sys
    ops = OperationsManager()
    sys.exit(ops.cmdloop())
