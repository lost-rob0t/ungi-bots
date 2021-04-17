#!/usr/bin/env python3

import cmd2
from utils.Config import config, list_index
import asyncio
from os import environ
import argparse
import re
import elasticsearch
from elasticsearch.helpers import scan
from utils.File_utils import write_csv, write_json

from utils.Elastic_Wrapper import (
    search
)
from utils.Sqlite3_Utils import log_user, hash_



user_fields = ["ut", "author", "op"]
content_list = ["m", "body", "text"]


async def run_search(host, query):
    await search(host, query)
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
        if site == "discord":
            x["username"] = i["ut"]
            x["source"] = i["sn"]
            x["website"] = "Discord"
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
    dump_parser.add_argument("-a", help="dump all users", action="store_true")
    dump_parser.add_argument("-c", help="Dump to csv file")
    dump_parser.add_argument("-j", help="Dump to json file")
    dump_parser.add_argument("-D", help="Dump to database", action="store_true", default=False)
    @cmd2.with_argparser(dump_parser)
    def do_dump_users(self, args):
        if args.d:
            discord_index = config("INDEX", "discord", self.config)
            data =  dump_users(self.es_host, "ut", discord_index, "discord")
            print(data)
            print("Dumping Discord Data, may take a while....")
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


if __name__ == "__main__":
    import sys
    loot = Looter()
    sys.exit(loot.cmdloop())
