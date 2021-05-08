#!/usr/bin/env python3

import cmd2, cmd2.ansi
from typing import List, Any
from utils.Config import config, list_index
import asyncio
from os import environ
import argparse
import re
import elasticsearch
from elasticsearch.helpers import scan
from ungi_utils.File_utils import write_csv, write_json

from ungi_utils.Elastic_Wrapper import (
    search
)
from ungi_utils.Sqlite3_Utils import log_user, hash_
from cmd2.table_creator import (
    BorderedTable,
    Column,
    HorizontalAlignment,
)

banner = """
                ___________)%%%%%%%%%/
               /%%%%%%%%%%/%{}%%%%%%/
              /{}%%%%%%%%/%%/%%%%%%/
             /%%\% _---_/ \/%%%%%%/
            /%%%%\/    /()|%%%%%%/
           /%%%%%|()  /+ /%%%%%%/
          /%%%%%%%\ +/HH%%\%%%%/
         /%%%%%%%/%HH/_/%%%\%%/
ejm97   /%%%%%%%/%%\/%%%%%%{}/
       /%%%%%%{}%%%/%%%%%%%%/
      /%%%%%%%%%%%/
     /
    /
   /
  /



"""

user_fields = ["ut", "author", "op"]
content_list = ["m", "body", "text", "title"]

def ansi_print(text):
    cmd2.ansi.style_aware_write(sys.stdout, text + '\n\n')


def build_search_table(content_type):
    """
    Used to Build the data table
    """
    columns: List[Column] = list()
    columns.append(Column("User", width=30,
                          header_horiz_align=HorizontalAlignment.CENTER,
                          data_horiz_align=HorizontalAlignment.CENTER))
    columns.append(Column("content", width=50,
                          header_horiz_align=HorizontalAlignment.CENTER,
                          data_horiz_align=HorizontalAlignment.LEFT))
    if content_type == "discord":
        columns.append(Column("channel", width=24,
                              header_horiz_align=HorizontalAlignment.CENTER,
                              data_horiz_align=HorizontalAlignment.CENTER))
        columns.append(Column("Server", width=30,
                              header_horiz_align=HorizontalAlignment.CENTER,
                              data_horiz_align=HorizontalAlignment.CENTER))
    else:
        columns.append(Column("Source", width=30,
                              header_horiz_align=HorizontalAlignment.CENTER,
                              data_horiz_align=HorizontalAlignment.CENTER))

    columns.append(Column("Date", width=28,
                          header_horiz_align=HorizontalAlignment.CENTER,
                          data_horiz_align=HorizontalAlignment.CENTER))
    if content_type == "reddit":
        columns.append(Column("Post Type", width=12,
                              header_horiz_align=HorizontalAlignment.CENTER,
                              data_horiz_align=HorizontalAlignment.CENTER))

    return columns

def content_search(es_host, index, search_term, site, limit=25):
    es = elasticsearch.Elasticsearch([es_host])

    if site == "discord" or "telegram":
        q = {
            "query": {
                "match": {
                    "m": search_term
            }}}
    if site == "reddit":
        q = {
            "query": {
                "multi_match": {
                    "query": search_term,
                    "fields": ["body", "post-title", "text"]
                }
            }
        }

    data = es.search(body=q, index=index, size=limit)
    return data
def search_by_user(es_host, index, username, site, limit=25):
    es = elasticsearch.Elasticsearch([es_host])
    if site == "discord" or "telegram":
        q = {"query": {"match": {"ut": username}}}
    if site == "reddit":
        q = {
            "query": {
                "multi_match": {
                    "query": username,
                    "fields": ["author", "op"]}}}

    data = es.search(body=q, index=index, size=limit)
    return data

def dump_users(es_host, field, index, site):
    es = elasticsearch.Elasticsearch([es_host])
    q = {
        "query": {
            "exists": {
                "field": field
            }
        }
    }


    data = scan(es, q, scroll="5m", index=index, size=10000)
    doc_dump = []
    print(f"Dumping {site} data, may take a while....")
    for i in data:
        i = i["_source"]
        x = {}
        if site == "discord" or "telegram":
            x["username"] = i["ut"]
            if site == "discord":
                x["source"] = i["sn"]
                x["website"] = "Discord"
            else:
                x["website"] = "Telegram"
                x["source"] = i["group"]
            x["hashid"] = hash_(x["username"] + x["source"])
            try:
                x["operation-id"] = i["operation-id"]
                doc_dump.append(x)
            except KeyError:
                continue
        if site == "reddit":
            try:
                x["username"] = i["op"]
            except KeyError:
                x["username"] = i["author"]
            x["source"] = i["subreddit"]
            x["website"] = "Reddit"
            x["hashid"] = hash_(x["username"] + x["source"])
            try:
                x["operation-id"] = i["operation-id"]
                doc_dump.append(x)
            except KeyError:
                pass
    deduped_docs = list({item["hashid"]: item for item in doc_dump}.values())
    return deduped_docs

class Looter(cmd2.Cmd):
    def __init__(self):
        super().__init__()
        self.color = True
        self.prompt = "ungi[looter]> "
        self.es_host = "http://127.0.0.1:9200"
        self.Id = 0
        try:
            self.config = environ['UNGI_CONFIG']
            self.database = config("DB", "path", self.config)
            self.es_host = config("ES", "host", self.config)
            self.indexes = list_index("INDEX", self.config)
        except KeyError as no_environ:
            try:
                self.config = "app.ini"
                self.database = config("DB", "path", self.config)
                self.es_host = config("ES", "host", self.config)
                self.indexes = list_index("INDEX", self.config)
            except FileNotFoundError as no_config:
                self.config = input("Config Not found!\npath to config: ")
                self.database = config("DB", "path", self.config)
                self.es_host = config("ES", "host", self.config)
                self.indexes = list_index("INDEX", self.config)
        self.add_settable(cmd2.Settable("Id", int, "Operation id to work with"))

    dump_parser = argparse.ArgumentParser()
    dump_parser.add_argument("-r", help="dump reddit users", action="store_true")
    dump_parser.add_argument("-d", help="dump discord users ", action="store_true")
    dump_parser.add_argument("-t", help="dump telegram telegram users", action="store_true")
    dump_parser.add_argument("-c", help="Dump to csv file")
    dump_parser.add_argument("-j", help="Dump to json file")
    dump_parser.add_argument("-D", help="Dump to database", action="store_true", default=False)
    @cmd2.with_argparser(dump_parser)
    def do_dump_users(self, args):
        if args.d:
            discord_index = config("INDEX", "discord", self.config)
            data =  dump_users(self.es_host, "ut", discord_index, "discord")
            if args.c:
                headers = ["username", "website", "source", "operation-id", "hashid"]
                write_csv(args.c, headers, data)
            if args.j:
                write_json(args.j, data)

            if args.D:
                for x in data:
                    log_user(self.database, x["username"], x["source"], "discord.com", x["operation-id"])

        # if the reddit flag is set
        if args.r:
            reddit_index = config("INDEX", "reddit", self.config)
            data = dump_users(self.es_host, "op", reddit_index, "reddit")
            data2 = dump_users(self.es_host, "author", reddit_index, "reddit")
            new_data = data + data2
            clean_docs = list({item["hashid"]: item for item in new_data}.values())

            # if csv flag is set
            if args.c:
                headers = ["username", "website", "source", "operation-id", "hashid"]
                write_csv(args.c, headers, clean_docs)
            # if the json flag is set
            if args.j:
                write_json(args.json, clean_docs)

            # save to database if the flag is set, will take a while
            if args.D:
                 for x in clean_docs:
                    try:
                        log_user(self.database, x["username"], x["source"], "reddit.com", x["operation-id"])
                    except KeyError as e:
                        print(e)

        if args.t:
            telegram_index = config("INDEX", "telegram", self.config)
            data = dump_users(self.es_host, "ut", telegram_index, "telegram")
            clean_docs = list({item["hashid"]: item for item in data}.values())

            # if csv flag is set
            if args.c:
                headers = ["username", "website", "source", "operation-id", "hashid"]
                write_csv(args.c, headers, clean_docs)
            # if the json flag is set
            if args.j:
                write_json(args.json, clean_docs)

            # save to database if the flag is set, will take a while
            if args.D:
                 for x in clean_docs:
                    try:
                        log_user(self.database, x["username"], x["source"], "telegram.com", x["operation-id"])
                    except KeyError as e:
                        print(e)
    search_parser = argparse.ArgumentParser()
    search_parser.add_argument("search_term", help="Search input")
    search_parser.add_argument("-t", help="Search telegram", action="store_true")
    search_parser.add_argument("-d", help="Search discord", action="store_true")
    search_parser.add_argument("-r", help="Search reddit", action="store_true")
    search_parser.add_argument("-D", help="dump users", action="store_true")
    search_parser.add_argument("-M", help="save messages to database", action="store_true")
    search_parser.add_argument("-m", help="save messages and users to csv")
    search_parser.add_argument("-l", help="limit number of results", default=25)
    search_parser.add_argument("-u", help="Search By username", action="store_true")
    @cmd2.with_argparser(search_parser)
    def do_search(self, args):
        if args.d:
            discord = config("INDEX", "discord", self.config)
            if args.u:
                data = search_by_user(self.es_host, discord, args.search_term, "discord", limit=args.l)
            else:
                data = content_search(self.es_host, discord, args.search_term, "discord", limit=args.l)
            data_list: List[List[List[Any]]] = list()
            for doc in data["hits"]['hits']:
                doc = doc["_source"]
                data_list.append([doc["ut"], doc["m"], doc["cn"], doc["sn"], doc["date"]])

            bt = BorderedTable(build_search_table("discord"))
            table = bt.generate_table(data_list)
            ansi_print(table)

            if args.D:
                for doc in data["hits"]["hits"]:
                    doc = doc["_source"]
                    try:
                        log_user(self.database, doc["ut"], doc["sn"], "discord.com", doc["operation-id"])
                    except KeyError:
                        print(f"server {doc['sn']} is not in the database\nSever id: {doc['sid']}")


        if args.r:
            reddit = config("INDEX", "reddit", self.config)
            if args.u:
                 data = search_by_user(self.es_host, reddit, args.search_term, "reddit", limit=args.l)
            else:
                data = content_search(self.es_host, reddit, args.search_term, "reddit", limit=args.l)
            data_list: List[List[List[Any]]] = list()
            for doc in data["hits"]['hits']:
                doc = doc["_source"]
                try:
                    data_list.append([doc["author"], doc["body"], doc["subreddit"], doc["date"], "Comment"])
                except KeyError:
                    try:
                        data_list.append([doc["op"], doc["text"], doc["subreddit"], doc["date"], "Post text"])
                    except KeyError:
                        try:
                            data_list.append([doc["op"], doc["post-title"], doc["subreddit"], doc["date"], "Post Name"])
                        except KeyError:
                            data_list.append([doc["op"], doc["link"], doc["subreddit"], doc["date"], "Post Link"])

            bt = BorderedTable(build_search_table("reddit"))
            table = bt.generate_table(data_list)
            ansi_print(table)

            if args.D:
                for doc in data["hits"]["hits"]:
                    doc = doc["_source"]
                    try:
                        log_user(self.database, doc["author"], doc["subreddit"], "reddit.com", doc["operation-id"])
                    except KeyError:
                        log_user(self.database, doc["op"], doc["subreddit"], "reddit.com", doc["operation-id"])
if __name__ == "__main__":
    import sys
    loot = Looter()
    sys.exit(loot.cmdloop())
