#!/usr/bin/env python3

import argparse
import discord
import requests
import datetime
import asyncio
import json
from ungi_cli.utils.Elastic_Wrapper import insert_doc
from ungi_cli.utils.Config import config
import hashlib
from os import environ
parser = argparse.ArgumentParser()
parser.add_argument("-t", "--token", help="Logs in with this token")
parser.add_argument("-d", "--db", help="database path")
parser.add_argument("-m", "--max", help="max history, dont go over 2000")
parser.add_argument("-c", "--connection", help="host", default="http://127.0.0.1:9200")
args = parser.parse_args()

oni = discord.Client()
conf_file = environ['UNGI_CONFIG']
index = config("INDEX", "discord", conf_file)
print(conf_file)
async def log_message(url, data):
    hash_input = bytes(str(data['m']) + str(data['date-nanos']) + str(data['sid']) + str(data['uid']), encoding='utf8')
    hash_id = hashlib.md5(hash_input).hexdigest()
    await insert_doc(args.connection, index, data, hash_id)

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
                    bot_test = message.author.bot
                    nickname = message.author.display_name
                    if bot_test is False:
                        md = {}
                        md['date-nanos'] = str(message.created_at.isoformat())
                        md['uid'] = str(message.author.id)
                        md['ut'] = str(message.author)
                        md['sn'] = str(message.guild)
                        md['sid'] = str(message.guild.id)
                        md['cn'] = str(message.channel)
                        md['cid'] = str(message.channel.id)
                        md['m'] = str(message.content)
                        await log_message(args.connection, md)
            except discord.errors.Forbidden as e:
                pass
            except AttributeError as e:
                pass
@oni.event
async def on_message(message):
    md = {}
    md['date-nanos'] = str(message.created_at.isoformat())
    md['uid'] = int(message.author.id)
    md['ut'] = str(message.author)
    md['sn'] = str(message.guild)
    md['sid'] = int(message.guild.id)
    md['cn'] = str(message.channel)
    md['cid'] = int(message.channel.id)
    md['m'] = str(message.content)
    await log_message(args.connection, md)
@oni.event
async def on_guild_join(guild):
    print(f'joined: {guild}')
    for channel in guild.channels:
        try:
            for message in await channel.history(limit=int(args.max)).flatten():
                bot_test = message.author.bot
                nickname = message.author.display_name
                if bot_test is False:
                    md = {}
                    md['date'] = str(message.created_at.isoformat())
                    md['uid'] = int(message.author.id)
                    md['ut'] = str(message.author)
                    md['sn'] = str(message.guild)
                    md['sid'] = int(message.guild.id)
                    md['cn'] = str(message.channel)
                    md['cid'] = int(message.channel.id)
                    md['m'] = str(message.content)
                    await log_message(args.connection, md)
        except discord.errors.Forbidden as e:
            pass
        except AttributeError as e:
            pass
@oni.event
async def on_guild_remove(guild):
    print(f'Left: {guild}')
    resp = await update(args.connection, 1)
try:
    oni.run(args.token, bot=False)
except KeyboardInterrupt as stop:
    print("Stopping!")
