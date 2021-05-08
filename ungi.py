#!/usr/bin/env python3
import sqlite3
import subprocess as sub
import cmd2
from ungi_utils.Config import config
from ungi_utils.Sqlite3_Utils import db_init
import argparse
from os import environ
# WARNING: THIS IS INSECURE DO NOT RUN IN PRODUCTION!!!


banner = """
╦ ╦╔╗╔╔═╗╦
║ ║║║║║ ╦║
╚═╝╝╚╝╚═╝╩
╦ ╦┌┐┌┌─┐┌─┐┌─┐┌┐┌
║ ║│││└─┐├┤ ├┤ │││
╚═╝┘└┘└─┘└─┘└─┘┘└┘
╔═╗┬┌─┐┌┐┌┌┬┐┌─┐
║ ╦│├─┤│││ │ └─┐
╚═╝┴┴ ┴┘└┘ ┴ └─┘
╦┌┐┌┌┬┐┌─┐┬  ┬  ┬┌─┐┌─┐┌┐┌┌─┐┌─┐
║│││ │ ├┤ │  │  ││ ┬├┤ ││││  ├┤
╩┘└┘ ┴ └─┘┴─┘┴─┘┴└─┘└─┘┘└┘└─┘└─┘
╔═╗┬─┐┌─┐┌┬┐┌─┐┬ ┬┌─┐┬─┐┬┌─
╠╣ ├┬┘├─┤│││├┤ ││││ │├┬┘├┴┐
╚  ┴└─┴ ┴┴ ┴└─┘└┴┘└─┘┴└─┴ ┴

          .  .
          dOO  OOb
         dOP'..'YOb
         OOboOOodOO
       ..YOP.  .YOP..
     dOOOOOObOOdOOOOOOb
    dOP' dOYO()OPOb 'YOb
        O   OOOO   O
    YOb. YOdOOOObOP .dOP
     YOOOOOOP  YOOOOOOP
       ''''      ''''



"""
print(banner)


class ungi(cmd2.Cmd):
    def __init__(self):
        super().__init__()
        self.color = True
        self.plugins = "./ungi_cli/"
        self.path = ""
        try:
            self.config = environ["UNGI_CONFIG"]
            self.database_path = config("DB", "path", self.config)
        except KeyError as no_val:
            try:
                self.config = "app.ini"
                self.database_path = config("DB", "path", self.config)
            except FileNotFoundError as no_config:
                self.config = input("Path to config: ")
                self.database_path = config("DB", "path", self.config)
        self.banner = 'banner.txt'
        self.prompt = 'ungi> '
        self.add_settable(cmd2.Settable('path', str, 'Path to the sqlite3 databse containing information'))
        self.add_settable(cmd2.Settable('prompt', str, 'Prompt to show'))
        self.add_settable(cmd2.Settable('plugins', str, 'Path to load pluins'))

    # This is Most certanly wrong way to do it.
    # Please pr a solution
    def do_run(self, *args):
        arg_list = []
        #full_run = plugin path + ".py"
        for arg in args:
            arg_list.append(arg)
        command = arg_list[0]
        arg_list[0] = f"{self.plugins}{command}.py"
        sub.run(arg_list, shell=True)


    init_parser = argparse.ArgumentParser()
    init_parser.add_argument("-p", help="database path")
    @cmd2.with_argparser(init_parser)
    def do_init(self, args):
        if args.p:
            self.database_path = args.p
        print("Setting up sqlite3 database")
        db_init(self.database_path, config("DB", "script", self.config))

    def do_manage(self, *args):
       sub.run([f"{self.plugins}/manage.py"])


if __name__ == '__main__':
    import sys
    c = ungi()
    sys.exit(c.cmdloop())
