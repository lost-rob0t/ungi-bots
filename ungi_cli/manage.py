#!/usr/bin/env python3

import argparse
import json
import cmd2
from  utils.Sqlite3_Utils import (
    delete_operation,
    add_discord,
    add_watch_word,
    add_subreddit,
    delete_operation,
    create_operation,
    update_target,
    get_op_id,
    get_op_name
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
    BorderedTable,
    Column,
    HorizontalAlignment,
)

def ansi_print(text):
    ansi.style_aware_write(sys.stdout, text + '\n\n')


class OperationsManager(cmd2.Cmd):
    def __init__(self):
        super().__init__()

        # we try and load the config from the environment
        # if the var is not set, we try and read from "app.ini"
        # if that fails ask the user for the path

        try:
            self.config_path = environ["UNGI_CONFIG"]
            self.database_path = config("DB", "path", environ["UNGI_CONFIG"])
        except KeyError as no_value:
            try:
                self.config_path = "app.ini"
                self.database_path = config("DB", "path", environ["UNGI_CONFIG"])
            except FileNotFoundError as no_config:
                self.config_path = input("Please input the path to config file: ")
                self.database_path = config("DB", "path", self.config_path)
        self.elastic_host = "http://127.0.0.1:9200"
        self.prompt = "Ungi[manage]> "
        self.add_settable(cmd2.Settable("database_path", str, "path to ungi database"))


    operations_parser = argparse.ArgumentParser()
    operations_parser.add_argument("-c", "--create")
    operations_parser.add_argument("-d", "--desc", help="Description for the Operation")
    operations_parser.add_argument("--remove", help="remove an Operation with all data and loot associated with it")
    @cmd2.with_argparser(operations_parser)
    def do_create(self, args):
        if args.remove:
            name = get_op_name(self.database_path, args.remove)[0]
            prompt = input(f"Are you sure you want to remove the operation: {name}?\n all data will be gone!\n(YES/NO): ")
            if prompt == "YES":
                delete_operation(self.database_path, args.remove)
                print("removed")
            elif prompt == "NO":
                print("Cancled")
            else:
                print("Type YES or NO")
        if args.create:
             print(f"Creating operation: {args.create}")
             create_operation(self.database_path, args.create, args.desc)



    # Setting up argparser
    list_parser = argparse.ArgumentParser()
    list_parser.add_argument("-r", help="Show Subreddits", action="store_true")
    list_parser.add_argument("-d", help="Show Discord Servers", action="store_true")
    list_parser.add_argument("-a", help="Show evrything", action="store_true")
    list_parser.add_argument("-o", help="Show ops", action="store_true")

    @cmd2.with_argparser(list_parser)
    def do_list(self, args):

        # If -o is used, we list operations

        if args.o:

            # Building Table
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

        if args.r:
            columns: List[Column] = list()
            columns.append(Column("Name", width=24,
                                  header_horiz_align=HorizontalAlignment.CENTER,
                                  data_horiz_align=HorizontalAlignment.CENTER))
            columns.append(Column("Operation", width=24,
                                  header_horiz_align=HorizontalAlignment.CENTER,
                                  data_horiz_align=HorizontalAlignment.CENTER))
            subs = list_subreddits(self.database_path)

            list_view: List[Any] = list()
            #Building the data that gos into the table
            for sub in subs:
                list_view.append([sub[1], get_op_name(self.database_path, sub[2])[0]])

            bt = BorderedTable(columns)
            table = bt.generate_table(list_view)
            ansi_print(table)

        if args.d:
            columns: List[Column] = list()
            columns.append(Column("Server_ID", width=24,
                                  header_horiz_align=HorizontalAlignment.CENTER,
                                  data_horiz_align=HorizontalAlignment.CENTER))
            columns.append(Column("Operation", width=24,
                                  header_horiz_align=HorizontalAlignment.CENTER,
                                  data_horiz_align=HorizontalAlignment.CENTER))
            servers = list_servers(self.database_path)


            list_view: List[Any] = list()

            #Building the data that gos into the table
            for server in servers:
                list_view.append([server[1], get_op_name(self.database_path, server[2])[0]])
            bt = BorderedTable(columns)
            table = bt.generate_table(list_view)
            ansi_print(table)


    # Setting up argparser
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
                add_subreddit(self.database_path, sub, op_id)
        else:
            print("Canceled")

    # Setting up argparser
    discord_bulk = argparse.ArgumentParser()
    discord_bulk.add_argument("-i", "--input", help="file containing discord id's")
    discord_bulk.add_argument("-Id", help="operation id")

    @cmd2.with_argparser(discord_bulk)
    def do_discord_bulk(self, args):
        columns: List[Column] = list()
        columns.append(Column("ID", width=12))
        columns.append(Column("Server ID", width=30,
                              header_horiz_align=HorizontalAlignment.CENTER, data_horiz_align=HorizontalAlignment.CENTER))
        reddit_list: List[List[Any]] = list()
        subreddits = []
        op_id = args.Id
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
                add_discord(self.database_path, sub, op_id)
        else:
            print("Canceled")


    # Setting up add parser
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

    target_parser = argparse.ArgumentParser()
    target_parser.add_argument("-u", help="username")
    target_parser.add_argument("-r", help="remove user from target list", action="store_true")
    target_parser.add_argument("-a", help="add user to target list", action="store_true")
    @cmd2.with_argparser(target_parser)
    def do_target(self, args):
        if args.a:
            print(args.u)
            prompt = input("Are you sure you want to add this user to the target list?\n(y/n): ")
            if prompt == "y":
                update_target(self.database_path, args.u, 1)
            else:
                print("canceled")

        else:
            print(args.u)
            prompt = input("Are you sure you want to remove this user from the target list?\n(y/n): ")
            if prompt == "y":
                update_target(self.database_path, args.u, 0)
            else:
                print("canceled")

if __name__ == '__main__':
    import sys
    ops = OperationsManager()
    sys.exit(ops.cmdloop())
