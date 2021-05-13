#!/usr/bin/env python3

import argparse
import discord
import datetime
import asyncio
import json
from ungi_utils.Elastic_Wrapper import insert_doc
from ungi_utils.Config import auto_load, UngiConfig
from ungi_utils.Sqlite3_Utils import list_servers, hash_, get_alert_level
from os import environ
parser = argparse.ArgumentParser()
parser.add_argument("-t", "--token", help="Logs in with this token")
parser.add_argument("-d", "--db", help="database path")
parser.add_argument("-m", "--max", help="max history, dont go over 2000")
parser.add_argument("--config", help="path to config")
parser.add_argument(

    "-c",
    "--connection",
    help="host",
    default="http://127.0.0.1:9200")
args = parser.parse_args()

oni = discord.Client()

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
for server in list_servers(database):

        server_watch = {}
        server_watch["id"] = server[1]
        server_watch["operation"] = server[2]
        server_watch["alert-level"] = get_alert_level(server[2])[0]
        print(server_watch)
        watch_list.append(server_watch)


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
    md = {}
    md['date'] = str(message.created_at.isoformat())
    md['uid'] = str(message.author.id)
    md['ut'] = str(message.author)
    md['sn'] = str(message.guild)
    md['sid'] = str(message.guild.id)
    md['cn'] = str(message.channel)
    md['cid'] = str(message.channel.id)
    md['m'] = str(message.content)
    md['nick'] = str(message.author.display_name)
    md['bot'] = str(message.author.bot)

    try:
        for id in watch_list:
            if id.get("id") == message.guild.id:
                md["operation-id"] = id["operation"]
    except KeyError as invalide_item:
        print(invalide_item)
    return md

# Ran at startup


@oni.event
async def on_ready():
    servers = 0
    channels = 0
    for guild in oni.guilds:
        servers += 1

    print(f'Watching: {servers} servers')
    for guild in oni.guilds:
        for channel in guild.channels:
            md_list = []
            try:
                for message in await channel.history(limit=int(args.max)).flatten():
                    channels += 1
                    md = doc_build(message)
                    await log_message(args.connection, md)
            except discord.errors.Forbidden as e:
                pass
            except AttributeError as e:
                pass


@oni.event
async def on_message(message):
    md = doc_build(message)
    await log_message(args.connection, md)


# ran when bot joins server
@oni.event
async def on_guild_join(guild):
    print(f'joined: {guild}')
    for channel in guild.channels:
        try:
            for message in await channel.history(limit=int(args.max)).flatten():
                md = doc_build(message)
                await log_message(args.connection, md)
        except discord.errors.Forbidden as e:
            pass
        except AttributeError as e:
            pass

# We start the bot.
# bot=False means it is started as a self bot

oni.run(args.token, bot=False)
