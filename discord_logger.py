#!/usr/bin/env python3

import argparse
import discord
import datetime
import asyncio
import json
import re
from ungi_utils.entity_utils import send_alert
from ungi_utils.Elastic_Wrapper import insert_doc
from ungi_utils.Config import auto_load, UngiConfig
from ungi_utils.Sqlite3_Utils import list_servers, hash_, get_alert_level, list_targets, get_words
from os import environ
from operator import itemgetter
parser = argparse.ArgumentParser()
parser.add_argument("-t", "--token", help="Logs in with this token")
parser.add_argument("-d", "--db", help="database path")
parser.add_argument("-m", "--max", help="max history, dont go over 2000")
parser.add_argument("--config", help="path to config")
parser.add_argument("-s", "--show", help="show servers the bot is in", action="store_true")
parser.add_argument(

    "-c",
    "--connection",
    help="host",
    default="http://127.0.0.1:9200")

args = parser.parse_args()

UngiBot = discord.Client()

# config stuff
config_file = auto_load(args.config)
conf_file = environ['UNGI_CONFIG']  # pulling config from environment
CONFIG = UngiConfig(conf_file)
database = CONFIG.db_path  # database path
# index setting where messages are stored
index = CONFIG.discord
print(conf_file)

# We are retreiving the list of servers in the watch list
watch_list = []
word_list = []
target_list = []
# TODO make this more logical
# maby make a list of tuples?
for server in list_servers(database):

        server_watch = {}
        server_watch["id"] = server[1]
        server_watch["operation-id"] = server[2]
        server_watch["alert-level"] = get_alert_level(CONFIG.db_path, server[2])[0]
        print(server_watch)
        watch_list.append(server_watch)

for word in get_words(CONFIG.db_path):
    word_d = {}
    word_d["word"] = word[0]
    word_d["operation-id"] = word[1]

for target in list_targets(CONFIG.db_path):
    target_d = {}
    target_d["target"] = target[0]
    target_d["operation-id"] = target[2]

async def log_message(url, data):
    hash_id = hash_(str(data['m']) +
                       str(data['date']) +
                       str(data['sid']) +
                       str(data['uid']))
    await insert_doc(args.connection, index, data, hash_id)


def doc_build(message):
    """
    Function used to build docs
    takes a discord message object as input
    """
    # TODO look for embeds
    # TODO save image links to doc
    md = {}
    md['date'] = str(message.created_at.isoformat())
    md['uid'] = str(message.author.id)
    md['ut'] = str(message.author)
    md['sn'] = str(message.guild)
    md['sid'] = str(message.guild.id)
    md['cn'] = str(message.channel)
    md['cid'] = str(message.channel.id)
    md['m'] = message.content
    md['nick'] = str(message.author.display_name)
    md['bot'] = str(message.author.bot)

    try:
        for id in watch_list:
            if abs(id.get("id")) == abs(message.guild.id):
                md["operation-id"] = id["operation-id"]
    except KeyError as invalide_item:
        print(invalide_item)

    return md

# Ran at startup

@UngiBot.event
async def on_ready():
    servers = 0
    for guild in UngiBot.guilds:
        if args.show:
            print(f"{guild.id}|{guild}")
        servers += 1

    print(f'Watching: {servers} servers')
    for guild in UngiBot.guilds:
        for channel in guild.channels:
            try:
                for message in await channel.history(limit=int(args.max)).flatten():
                    md = doc_build(message)
                    await log_message(args.connection, md)
            except discord.errors.Forbidden:
                pass
            except AttributeError:
                pass
            
# Ran When a new message is sent to the ungi bot

@UngiBot.event
async def on_message(message):
    md = doc_build(message)
    min_level = 0
    try:
        for watch in watch_list:
            if watch["operation-id"] == md["operation-id"]:
                min_level = int(watch["alert-level"])
                print(md)
                break
    except KeyError as e:
        print(e)
        print(f"{md['sn']}: is not in the UNGI db")
    
    try:
        if 20 >= min_level:
            if md["oepration-id"]:
                    send_alert(str(md["m"]), md["nick"], md["sn"], "new_message", str(f"{CONFIG.server_host}:{CONFIG.server_port}/alert"))
    except KeyError as e:
        print(e)
    try:
        for target in target_list:
            if target["target"] == md["ut"]:
                if 75 >= min_level:
                        if md["oepration-id"]:
                                send_alert(str(md["m"]), md["nick"], md["sn"], "target", str(f"{CONFIG.server_host}:{CONFIG.server_port}/alert"))
    except KeyError:
        pass
    for word in word_list:
        try:
            r = re.match(word, md["m"])
            if r:
                source = md["sn"] + " | " + r
                if 85>= min_level:
                    send_alert(md["m"], md["nick"], source, "watch_word", str(f"{CONFIG.server_host}:{CONFIG.server_port}/alert"))
        except KeyError:
            pass



    await log_message(args.connection, md)


# ran when bot joins server
@UngiBot.event
async def on_guild_join(guild):
    print(f'joined: {guild}')
    for channel in guild.channels:
        try:
            for message in await channel.history(limit=int(args.max)).flatten():
                md = doc_build(message)
                await log_message(args.connection, md)
        except discord.errors.Forbidden:
            pass
        except AttributeError:
            pass

# We start the bot.
# Note: This only works in discord.py-self pkg becuase discord removed self bots

UngiBot.run(args.token)
