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
from telethon.errors.rpcerrorlist import ChatAdminRequiredError
async def log_message(es_host, index, input_dict):
    hash_id = hash_(str(
        str(input_dict["m"]) +
        str(input_dict["ut"]) +
        str(input_dict["date"]) +
        str(input_dict["group"])))

    await insert_doc(es_host, index, input_dict, hash_id)

async def doc_builder(event_obj, client, chat_list):
    doc = {}

    doc["m"] = event_obj.message.raw_text
    doc["date"] = str(event_obj.date.now().isoformat())
    doc["sender-id"] = str(abs(event_obj.sender_id))
    try:
        username = await client.get_entity(event_obj.sender_id)
        doc["ut"] = username.username
    except ValueError as e:
        username = await client.get_entity(PeerUser(abs(event_obj.sender_id)))
        doc["ut"] = username.username

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

def get_id(chats, client):
    chat_ids = []
    chats.append("UNGI9090")
    for chat in chats:
        id = client.get_peer_id(chat)
        chat_ids.append(id)
    return chat_ids

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
    api_id = config("TELEGRAM", "api_id", config_file)
    api_hash = config("TELEGRAM", "api_hash", config_file)
    api_session_file = config("TELEGRAM", "session_file", config_file)
    database = config("DB", "path", config_file)
    es_host = config("ES", "host", config_file)
    media_path = config("TELEGRAM", "media", config_file)
    ocr_path = config("OCR", "path", config_file)
    client =  TelegramClient(api_session_file, api_id, api_hash)

    # We are retreiving the list of servers in the watch list
    watch_list = []
    chats = []
    for chat in list_telegram(database):
        chat_watch = {}
        chat_watch["id"] = chat[1]
        chat_watch["operation"] = chat[2]
        chats.append(chat_watch["id"])
        watch_list.append(chat_watch)

    chat_ids = get_id(chats, client)


    @client.on(events.NewMessage(chats=chat_ids))
    async def newMessage(event):
        d = await doc_builder(event, client, watch_list)
        await log_message(es_host, telegram_index, d)
        print(d)
        if event.message.media:
            print("saving image: " + media_path + str(datetime.datetime.now().isoformat()) + ".jpg")
            await client.download_media(event.message.media, media_path + str(datetime.datetime.now().isoformat()) + ".jpg")
    with client:
        for chat in chat_ids:
            try:
                client.get_participants(chat)
            except ChatAdminRequiredError:
                pass
        client.run_until_disconnected()
main()
