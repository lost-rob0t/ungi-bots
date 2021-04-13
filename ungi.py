#!/usr/bin/env python3
import sqlite3
import subprocess as sub
import cmd2

# WARNING: THIS IS INSECURE DO NOT RUN IN PRODUCTION!!!

class ungi(cmd2.Cmd):
    def __init__(self):
        super().__init__()
        self.color = True
        self.plugins = "./ungi_cli/"
        self.path = ""
        self.banner = 'banner.txt'
        self.prompt = 'ungi> '
        self.add_settable(cmd2.Settable('path', str, 'Path to the sqlite3 databse containing information'))
        self.add_settable(cmd2.Settable('prompt', str, 'Prompt to show'))
        self.add_settable(cmd2.Settable('plugins', str, 'Path to load pluins'))

    def do_run(self, *args):
        arg_list = []
        #full_run = mod + ".py"
        for arg in args:
            arg_list.append(arg)
        command = arg_list[0]
        arg_list[0] = f"{self.plugins}{command}.py"
        sub.run(arg_list, shell=True)


if __name__ == '__main__':
    import sys
    c = ungi()
    sys.exit(c.cmdloop())
