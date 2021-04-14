#!/usr/bin/env python3

from configparser import ConfigParser

"""
This handles all of our config needs for UNGI
"""

def config(section, option, filename):
    parser = ConfigParser()
    parser.read(filename)
    if parser.has_section(section):
        val = parser.get(section, option)
        return val

def list_index(section, filename):
    parser = ConfigParser()
    parser.read(filename)
    index_list = []
    for x in parser[f"{section}"]:
        index_list.append(parser.get(f"{section}", x))
    return index_list
    #for index in parser[section]:

#def list_indexes(section, filename):

#    parser = ConfigParser()
#    parser.read(filename)
#    index_list = []
#    if parser.has_section(section):
#        for val in parser.se

