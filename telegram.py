#!/usr/bin/env python3

#!/usr/bin/env python3
from ungi_cli.utils.Elastic_Wrapper import insert_doc
from ungi_cli.utils.Sqlite3_Utils import hash_, list_telegram
from ungi_cli.utils.Config import config
import os
import datetime
from telethon import TelegramClient, events, sync, utils
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel, PeerUser, PeerChat, Photo
from telethon.errors.rpcerrorlist import ChatAdminRequiredError, ChannelPrivateError
import asyncio
import argparse
from time import sleep
from random import shuffle
import pytz

# i got this from here
# https://stackoverflow.com/questions/4563272/convert-a-python-utc-datetime-to-a-local-datetime-using-only-python-standard-lib


def utc_to_local(utc_dt):
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)  # .normalize might be unnecessary


# We return date as iso format
def aslocaltimestr(utc_dt):
    return utc_to_local(utc_dt).isoformat()

# we log message using this
# hash is based on message + username + group + date


async def log_message(es_host, index, input_dict):
    try:
        hash_id = hash_(str(
            str(input_dict["m"]) +
            str(input_dict["ut"]) +
            str(input_dict["date"]) +
            str(input_dict["group"])))

        await insert_doc(es_host, index, input_dict, hash_id)
    except KeyError as bad_doc:
        print(bad_doc)

# used to build the docs from message objects


async def doc_builder(message, client, chat_list):
    doc = {}
    if message.sender_id:
        if message.message:
            #fixed_date = datetime.datetime.strftime(message.date, "%Y-%m-%d %H:%M:%S.%f")
            fixed_date = str(aslocaltimestr(message.date))
            doc["m"] = message.raw_text
            doc["date"] = fixed_date
            # print(str(message.date.now()))
            doc["sender-id"] = str(abs(message.sender_id))
            try:
                username = await client.get_entity(abs(message.sender_id))
                doc["ut"] = username.username
                group = await client.get_entity(abs(message.peer_id.channel_id))
                doc["group"] = group.title
            except ValueError as e:
                username = await client.get_entity(PeerUser(abs(message.sender_id)))
                doc["ut"] = username.username
                print(username)
                group = await client.get_entity(abs(message.peer_id.channel_id))
                if group is None:
                    doc["group"] = doc["ut"]
                else:
                    doc["group"] = group.title
                for chat_name in chat_list:
                    name = chat_name["id"]
                    if group.username == name:
                        doc["operation-id"] = chat_name["operation"]

    return doc


async def get_id(chats, client):
    """
    used to get the id for each chat.
    returns a a list of acess hashes
    """
    chat_ids = []
    for chat in chats:
        try:
            id = await client.get_peer_id(chat)
            real_id, peer_type = utils.resolve_id(abs(id))
            chat_ids.append(abs(real_id))
        except ValueError:
            try:
                id = await client.get_entity(chat)
                real_id, peer_type = utils.resolve_id(abs(id))
                chat_ids.append(abs(real_id))
            except ValueError:
                chat = "t.me/joinchat/" + chat
                print(chat)
                group_chat = await client.get_entity(chat)
                print(abs(group_chat.access_hash))
                if group_chat.access_hash != 0:
                    real_id, peer_type = utils.resolve_id(
                        abs(group_chat.access_hash))
                    chat_ids.append(abs(real_id))
    return chat_ids


async def get_messages(client, es_host, index, chats, watch_list):
    """
    Used to grab all available messages
    """
    for chat in chats:
        try:
            async for message in client.iter_messages(chat):
                d = await doc_builder(message, client, watch_list)
                await log_message(es_host, index, d)
                if media_path:
                    try:
                        if message.media.photo:
                            try:
                                path = media_path + str(aslocaltimestr(message.date)) + f"_{d['group']}.jpg"
                            except KeyError:
                                path = media_path + \
                                    str(aslocaltimestr(message.date)) + ".jpg"
                            if os.path.exists(path):
                                print("Duplicate file: " + path)
                            else:
                                await client.download_media(message.media, path)
                    except AttributeError as e:
                        pass  # bad yes, but no error spam.

        except ChannelPrivateError:
            print(f"{chat} is private")

        print("done, waiting to avoid timeouts")
        sleep(1)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to config file")
    parser.add_argument(
        "-f",
        "--full",
        help="Get complete Chat Histories",
        action="store_true")
    args = parser.parse_args()

    global config_file
    # we try to load config path from enviroment first
    try:
        config_file = args.config
    except KeyError as no_env:
        config_file = os.environ["UNGI_CONFIG"]

    # config setup
    # TODO create a class for this
    telegram_index = config("INDEX", "telegram", config_file)
    api_id = config("TELEGRAM", "api_id", config_file)
    api_hash = config("TELEGRAM", "api_hash", config_file)
    api_session_file = config("TELEGRAM", "session_file", config_file)
    database = config("DB", "path", config_file)
    es_host = config("ES", "host", config_file)
    global media_path
    media_path = config("TELEGRAM", "media", config_file)
    ocr_path = config("OCR", "path", config_file)
    timezone = config("TIME", "timezone", config_file)
    client = TelegramClient(api_session_file, api_id, api_hash)

    global local_tz
    local_tz = pytz.timezone(timezone)
    # We are retreiving the list of servers in the watch list
    watch_list = []
    chats = []

    for chat in list_telegram(database):
        chat_watch = {}
        chat_watch["id"] = chat[1]
        chat_watch["operation"] = chat[2]
        chats.append(chat_watch["id"])
        watch_list.append(chat_watch)

    async with client:
        chat_ids = await get_id(chats, client)
        shuffle(chat_ids)  # randomized
        dialogs = await client.get_dialogs()

        if args.full:
            await get_messages(client, es_host, telegram_index, chat_ids, watch_list)
            print("done, waiting to avoid timeouts")

        @client.on(events.NewMessage(chats=chat_ids))
        async def newMessage(event):
            d = await doc_builder(event.message, client, watch_list)
            await log_message(es_host, telegram_index, d)
            if media_path:
                try:
                    if event.message.media.photo:
                        try:
                            path = media_path + str(aslocaltimestr(message.date)) + f"_{d['group']}.jpg"
                        except KeyError:
                            path = media_path + \
                                str(aslocaltimestr(message.date)) + ".jpg"
                            if os.path.exists(path):
                                print("Duplicate file: " + path)
                            else:
                                await client.download_media(event.message.media, path)
                except AttributeError as e:
                    pass  # bad yes, but no error spam.
        await client.run_until_disconnected()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
