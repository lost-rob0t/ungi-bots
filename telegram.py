#!/usr/bin/env python3

#!/usr/bin/env python3
from ungi_cli.utils.Elastic_Wrapper import insert_doc
from ungi_cli.utils.Sqlite3_Utils import hash_, list_telegram

from ungi_cli.utils.Config import config
from os import environ
import datetime

from telethon.errors import SessionPasswordNeededError
from telethon import TelegramClient, events, sync
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel, PeerUser, PeerChat
)
import asyncio
import argparse

async def log_message(es_host, index, input_dict):
    hash_id = hash_(str(
        input_dict["m"] +
        input_dict["ut"] +
        input_dict["date"] +
        input_dict["group"]))

    await insert_doc(es_host, index, input_dict, hash_id)

async def doc_builder(event_obj, client, chat_list):
    doc = {}
    doc["m"] = event_obj.message.message
    doc["date"] = str(event_obj.date.now())
    doc["sender-id"] = str(abs(event_obj.sender_id))
    try:
        username = await client.get_entity(event_obj.sender_id)
        doc["ut"] = username.username
    except Exception as e:
        print(e)

    try:
         group = await client.get_entity(event_obj.peer_id.channel_id)
         doc["group"] = group.username
         for chat_name in chat_list:
             name = chat_name["id"]
             if group.username == name:
                 doc["operation-id"] = chat_name["operation"]
    except Exception as e:
        print(e)
    return doc

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to config file")
    parser.add_argument("-f", "--full", help="Get complete Chat Histories")
    args = parser.parse_args()

    # we try to load config path from enviroment first
    try:
        config_file = environ["UNGI_CONFIG"]
    except KeyError as no_env:
        config_file = args.config

    # config setup
    telegram_index = config("INDEX", "telegram", config_file)
    api_id = config("telegram", "api_id", config_file)
    api_hash = config("telegram", "api_hash", config_file)
    api_session_file = config("telegram", "session_file", config_file)
    database = config("DB", "path", config_file)
    es_host = config("ES", "host", config_file)

    # We are retreiving the list of servers in the watch list
    watch_list = []
    for chat in list_telegram(database):
        chat_watch = {}
        chat_watch["id"] = chat[1]
        chat_watch["operation"] = chat[2]
        watch_list.append(chat_watch)

    # client setup
    client =  TelegramClient(api_session_file, api_id, api_hash)
    @client.on(events.NewMessage(chats=channel_in))
    async def newMessage(event):
        d = await doc_builder(event, client, watch_list)
        await log_message(es_host, telegram_index, d)
        print(d)
    with client:
        client.run_until_disconnected()
    client.get_input_entity()
main()
