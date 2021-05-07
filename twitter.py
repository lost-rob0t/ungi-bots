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

def utc_to_local(utc_dt):
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)  # .normalize might be unnecessary


# We return date as iso format
def aslocaltimestr(utc_dt):
    return utc_to_local(utc_dt).isoformat()

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
        c.Hide_output = q
        twint.run.Lookup(c)
        info = twint.storage.panda.User_df
        d = doc_build("info", info, target["operation-id"])
        asyncio.run(insert_doc(es_host, index, d, d["id"]))

def get_user(username, index, es_host, operation_id):
    c = twint.Config
    c.Username = username
    c.Pandas = True
    twint.run.Lookup(c)
    info = twint.storage.panda.User_df
    d = doc_build("info", info, operation_id)

def get_timeline(target_list, es_host, index, limit):
    for target in target_list:
        t = []
        c = twint.Config()
        c.Username = target["username"]
        c.Limit = limit
        c.Hide_output = q
        c.Pandas = True
        #c.Store_object = True
        #c.Store_object_tweets_list = t
        #c.Store_object_tweets_list = True
        twint.run.Profile(c)
        data = twint.storage.panda.Tweets_df
        for tweet_data in data.itertuples():
            d = doc_build("tweet", tweet_data, target["operation-id"])
            asyncio.run(insert_doc(es_host, index, d, d["id"]))
def doc_build(d_type, panda_in, operation_id):
    """
    function used to build docs.
    Inputs:
    d_type (type of input)
    panda_in is the data input
    """
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
        #doc["backround"] = panda_in["backround_image"]

        return doc
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
        #doc["convo"] =
        d = datetime.datetime.strptime(panda_in.date, "%Y-%m-%d %H:%M:%S").isoformat()
        doc["date"] = str(d)
        doc["id"] = hash_(doc["username"] + doc["date"] + doc["m"])
        return doc


#get_user_info(get_twitters("/home/user/git/ungi/db/snake.db"))
#get_timeline(get_twitters("/home/user/git/ungi/db/snake.db"), "kek", "kek", "kek")

def main():
    global q
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--full", help="Grab everything")
    parser.add_argument("-c", "--config", help="path to config")
    parser.add_argument("-s", "--show", help="Show Targets")
    parser.add_argument("-l", "--limit", help="Max tweets to pull", default=25)
    parser.add_argument("-u", "--update", help="update user profile info")
    parser.add_argument("-q", default="True", action="store_false")
    args = parser.parse_args()
    q = args.q
    global local_tz
    CONFIG = UngiConfig(auto_load(args.config))
    local_tz = CONFIG.timezone
    targets = get_twitters(CONFIG.db_path)

    if args.show:
        t = len(targets)
        print(f"watching {t} users....")
        for target in targets:
            print(target["username"])
    if args.full:
        get_users(targets, CONFIG.twitter, CONFIG.es_host)
        get_timeline(targets, CONFIG.es_host, CONFIG.twitter, args.limit)

    if args.update:
        get_users(targets, CONFIG.twitter, CONFIG.es_host)
        get_timeline(targets, CONFIG.es_host, CONFIG.twitter, args.limit)
main()
