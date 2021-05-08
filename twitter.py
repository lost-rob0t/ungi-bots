#!/usr/bin/env python3

import argparse
import twint
import pandas
from ungi_utils.Sqlite3_Utils import list_twitter, hash_
from ungi_utils.Elastic_Wrapper import insert_doc
from ungi_utils.Config import UngiConfig, auto_load
import json
import asyncio
import pytz
import datetime
import os
import typing
import concurrent.futures
import itertools


def chunked(list_in, size):
    """
    function used to split up list to give to multithreader
    TODO Move this to ungi_utils pkg
    Inputs:
    list_in: (list_in)
    size: size of each chunk (int)
    NOTE if the list legnth is indivisble by chunk then the last chunk
    will be smaller than chunk size
    """

    # adapted from:
    # https://stackoverflow.com/questions/8991506/iterate-an-iterator-by-chunks-of-n-in-python
    """Generate sequences of `chunk_size` elements from `iterable`."""
    iterable = iter(list_in)
    while True:
        chunk = []
        try:
            for _ in range(size):
                chunk.append(next(iterable))
            yield chunk
        except StopIteration:
            if chunk:
                yield chunk
            break


def get_twitters(path):
    data = list_twitter(path)
    watch_list = []
    # We are iterating over the returned records.
    # Username is index 0 and operation-id is index 1
    for record in data:
        twit_d = {}
        twit_d["username"] = record[0]
        twit_d["operation-id"] = record[1]
        watch_list.append(twit_d)

    return watch_list


def get_users(target_list, index, es_host):
    """
    used to fetch user information
    iterates over the input list of tuples
    """
    for target in target_list:
        username = target["username"]
        c = twint.Config
        c.Username = username
        c.Pandas = True
        c.Hide_output = verbose
        twint.run.Lookup(c)
        info = twint.storage.panda.User_df
        d = doc_build("info", info, target["operation-id"])
        asyncio.run(insert_doc(es_host, index, d, d["id"]))


def get_timeline(target_list, es_host, index, limit):
    for target in target_list:
        t = []
        c = twint.Config()
        c.Username = target["username"]
        c.Limit = limit
        c.Hide_output = verbose
        c.Pandas = True
        c.Retries_count = 3
        c.Pandas_au = True
        c.Pandas_clean = True
        twint.run.Search(c)
        data = twint.storage.panda.Tweets_df
        d_list = []

        data = twint.storage.panda.Tweets_df
        for tweet_data in data.itertuples():
            d = doc_build("tweet", tweet_data, target["operation-id"])
            d_list.append(d)
        for doc in d_list:
            asyncio.run(insert_doc(es_host, index, doc, doc["id"]))
def doc_build(d_type, panda_in, operation_id):
    """
    function used to build docs.
    Inputs:
    d_type (type of input)
    panda_in is the data input
    """

    # If theis is an acount info pandas
    if d_type == "info":
        doc = {}
        doc["operation-id"] = operation_id
        doc["bio"] = panda_in.bio[0]
        doc["bio-url"] = panda_in.url[0]
        doc["name"] = panda_in.name[0]
        doc["user-id"] = panda_in.id[0]
        doc["username"] = panda_in.username[0]
        doc["private"] = str(panda_in.private[0])
        doc["verified"] = str(panda_in.verified[0])
        doc["avatar"] = panda_in.avatar[0]
        doc["id"] = hash_(doc["name"] + doc["bio-url"] + doc["username"] + doc["bio"] + doc["avatar"])

        return doc
    # if this is a tweet pandas
    else:
        doc = {}
        doc["operation-id"] = operation_id
        doc["tweet-id"] = panda_in.id
        doc["geo"] = panda_in.geo
        doc["link"] = panda_in.link
        doc["urls"] = panda_in.urls
        doc["photos"] = panda_in.photos
        doc["retweet"] = panda_in.retweet
        doc["place"] = panda_in.place
        doc["day"] = panda_in.day
        doc["username"] = panda_in.username
        doc["name"] = panda_in.name
        doc["m"] = panda_in.tweet
        d = datetime.datetime.strptime(panda_in.date, "%Y-%m-%d %H:%M:%S").isoformat()
        doc["date"] = str(d)
        doc["id"] = hash_(doc["username"] + doc["date"] + doc["m"])
        return doc


def update(list_in, index, es_host, limit):

    get_users(list_in, index, es_host)
    get_timeline(list_in, es_host, index, limit)

def main():
    global verbose
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--full", help="Grab everything", action="store_true")
    parser.add_argument("-c", "--config", help="path to config")
    parser.add_argument("-s", "--show", help="Show Targets", action="store_true")
    parser.add_argument("-l", "--limit", help="Max tweets to pull", default=25)
    parser.add_argument("-u", "--update", help="update user profile info", action="store_true")
    parser.add_argument("-v", "--verbose", default="True", action="store_false")
    parser.add_argument("-m", "--max", default=3)
    args = parser.parse_args()
    verbose = args.verbose
    global local_tz
    CONFIG = UngiConfig(auto_load(args.config))
    local_tz = CONFIG.timezone
    data = chunked(get_twitters(CONFIG.db_path), 2)
    users = get_twitters(CONFIG.db_path)
    if args.show:
        t = len(users)
        print(f"watching {t} users....")
        for user in users:
            print(user["username"])
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(args.max)) as executor:
        twitter_bots = {executor.submit(update, chunk, CONFIG.twitter, CONFIG.es_host, args.limit): chunk for chunk in data}
main()
