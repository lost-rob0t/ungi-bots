#!/usr/bin/env python3

import argparse
import json
import cmd2
from  ungi_utils.Sqlite3_Utils import (
    delete_operation,
    add_discord,
    add_watch_word,
    add_subreddit,
    delete_operation,
    create_operation,
    update_target,
    get_op_id,
    get_op_name,
    add_telegram,
    list_ops,
    list_servers,
    list_telegram,
    list_subreddits,
    add_twitter,
    move_twitter,
    list_twitter
    )

from ungi_utils.Config import config
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


# TODO make it pep8


def ansi_print(text):
    ansi.style_aware_write(sys.stdout, text + '\n\n')


def create_list_table(content_type):
    columns: List[Column] = list()
    if content_type == "operations":
        """
        Builds Operations listing.
        """

        columns.append(Column("ID", width=12,
                              header_horiz_align=HorizontalAlignment.CENTER,
                              data_horiz_align=HorizontalAlignment.CENTER))
        columns.append(Column("Name", width=30,
                              header_horiz_align=HorizontalAlignment.CENTER,
                              data_horiz_align=HorizontalAlignment.CENTER))
        columns.append(Column("Description", width=30,
                              header_horiz_align=HorizontalAlignment.CENTER,
                              data_horiz_align=HorizontalAlignment.CENTER))

    if content_type == "source":
        """
        Builds the normal source table
        used for discord, reddit
        """
        columns.append(Column("Name", width=24,
                              header_horiz_align=HorizontalAlignment.CENTER,
                              data_horiz_align=HorizontalAlignment.CENTER))
        columns.append(Column("Operation", width=24,
                              header_horiz_align=HorizontalAlignment.CENTER,
                              data_horiz_align=HorizontalAlignment.CENTER))


    if content_type == "telegram":
        """
        Builds telegram chat table
        Needed because you need to see the
        "channel id" and the channel name/title
        """

        columns.append(Column("Channel ID", width=20,
                              header_horiz_align=HorizontalAlignment.CENTER,
                              data_horiz_align=HorizontalAlignment.CENTER))
        columns.append(Column("Name", width=30,
                              header_horiz_align=HorizontalAlignment.CENTER,
                              data_horiz_align=HorizontalAlignment.CENTER))
        columns.append(Column("Operation", width=24,
                              header_horiz_align=HorizontalAlignment.CENTER,
                              data_horiz_align=HorizontalAlignment.CENTER))



    return columns


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
    operations_parser.add_argument("create", help="Input name")
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
             if args.desc is None:
                 args.desc = "No Description"
             create_operation(self.database_path, args.create, args.desc)



    # Setting up argparser
    list_parser = argparse.ArgumentParser()
    list_parser.add_argument("-r", help="Show Subreddits", action="store_true")
    list_parser.add_argument("-d", help="Show Discord Servers", action="store_true")
    list_parser.add_argument("-o", help="Show ops", action="store_true")
    list_parser.add_argument("-t", help="telgram", action="store_true")
    list_parser.add_argument("-T", help="twitter", action="store_true")
    @cmd2.with_argparser(list_parser)
    def do_ls(self, args):

        # If -o is used, we list operations

        if args.o:

            # Building Table
            columns = create_list_table("operations")

            ops = list_ops(self.database_path)
            data_list: List[List[Any]] = list()
            for op in ops:
                data_list.append([op[0], op[1], op[2]])

            bt = BorderedTable(columns)
            table = bt.generate_table(data_list)
            ansi_print(table)

        if args.r:
            columns = create_list_table("source")
            subs = list_subreddits(self.database_path)

            list_view: List[Any] = list()
            #Building the data that gos into the table
            for sub in subs:
                list_view.append([sub[1], get_op_name(self.database_path, sub[2])[0]])

            bt = BorderedTable(columns)
            table = bt.generate_table(list_view)
            ansi_print(table)

        if args.d:
            columns = create_list_table("source")
            servers = list_servers(self.database_path)


            list_view: List[Any] = list()

            #Building the data that gos into the table
            for server in servers:
                list_view.append([server[1], get_op_name(self.database_path, server[2])[0]])
            bt = BorderedTable(columns)
            table = bt.generate_table(list_view)
            ansi_print(table)

        if args.t:
            columns = create_list_table("telegram")
            servers = list_telegram(self.database_path)


            list_view: List[List[Any]] = list()

            #Building the data that gos into the table
            for server in servers:
                list_view.append([server[0], server[1], get_op_name(self.database_path, server[2])[0]])
            bt = BorderedTable(columns)
            table = bt.generate_table(list_view)
            ansi_print(table)

        if args.T:
            columns = create_list_table("source")
            users = list_twitter(self.database_path)

            list_view: List[Any] = list()

            for user in users:
                list_view.append([user[0], get_op_name(self.database_path, user[1])[0]])
            bt = BorderedTable(columns)
            table = bt.generate_table(list_view)
            ansi_print(table)


    # Setting up add parser
    add_parser = argparse.ArgumentParser()
    add_parser.add_argument("-d", help="Discord", action="store_true")
    add_parser.add_argument("-r", help="Reddit", action="store_true")
    add_parser.add_argument("-Id", help="Operation id")
    add_parser.add_argument("input", help="input")
    add_parser.add_argument("-t", help="add a telegram link", action="store_true")
    add_parser.add_argument("-T", help="add a twitter user", action="store_true")
    @cmd2.with_argparser(add_parser)
    def do_add(self, args):
        print(f"adding {args.input}")
        choice = input("is this ok? (y/n): ")
        if choice.lower() == "y" or choice == "yes":
            if args.d:
                add_discord(self.database_path, args.input, args.Id)

            if args.r:
                add_subreddit(self.database_path, args.input, args.Id)

            if args.t:
                add_telegram(self.database_path, args.input, args.Id)

            if args.T:
                add_twitter(self.database_path, args.input, args.Id)
        else:
            print("canceled")

    target_parser = argparse.ArgumentParser()
    target_parser.add_argument("u", help="username")
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

    bulk_parser = argparse.ArgumentParser()
    bulk_parser.add_argument("input", help="Path to input File")
    bulk_parser.add_argument("-Id", help="operation id")
    bulk_parser.add_argument("-d", help="add discord servers in bulk", action="store_true")
    bulk_parser.add_argument("-r", help="add subreddits in bulk", action="store_true")
    bulk_parser.add_argument("-t", help="add telegram in bulk", action="store_true")
    bulk_parser.add_argument("-T", help="add twitter users in bulk", action="store_true")
    @cmd2.with_argparser(bulk_parser)
    def do_bulk(self, args):
        columns = create_list_table("source")
        data_list: List[List[Any]] = list()
        with open(args.input, "r") as input_file:
            for line in input_file:
                data_list.append([line, get_op_name(self.database_path, args.Id)[0]])
        bt = BorderedTable(columns)
        table = bt.generate_table(data_list)
        ansi_print(table)
        prompt = input("Is this ok?\n(YES/NO)")
        if prompt == "YES" or prompt == "yes":
            if args.d:
                with open(args.input, "r") as input_file:
                    for line in input_file:
                        add_discord(self.database_path, line, args.Id)
            if args.r:
                with open(args.input, "r") as input_file:
                    for line in input_file:
                        add_subreddit(self.database_path, line, args.Id)
            if args.t:
                with open(args.input, "r") as input_file:
                    for line in input_file:
                        try:
                            chan_id, name = line.split("|")
                        except ValueError:
                            name = input(f"Name for {chan_id}?: ")
                        add_telegram(self.database_path, chan_id, args.Id, name)

            if args.T:
                with open(args.input, "r") as input_file:
                    for line in input_file:
                        add_twitter(self.database_path, line.rstrip(), args.Id)


        if prompt == "NO" or "no":
            print("canceled")

if __name__ == '__main__':
    import sys
    ops = OperationsManager()
    sys.exit(ops.cmdloop())
