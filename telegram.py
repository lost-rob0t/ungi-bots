#!/usr/bin/env python3

#!/usr/bin/env python3
from ungi_cli.utils.Elastic_Wrapper import insert_doc
from ungi_cli.utils.Sqlite3_Utils import hash_, list_telegram
from ungi_cli.utils.Config import auto_load, UngiConfig
from ungi_cli.utils.entity_utils import extract_ent, get_hashtags, fix_up
import os
import datetime
from telethon import TelegramClient, events, sync, utils
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel, PeerUser, PeerChat, Photo
from telethon.errors.rpcerrorlist import ChatAdminRequiredError, ChannelPrivateError, FloodWaitError
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
    if message:
        sender_data = await message.get_sender()
        chat_data = await message.get_chat()
        doc["group"] = chat_data.title

        try:
            doc["ut"] = sender_data.username
        except AttributeError:

            fn = getattr(sender_data, "first_name", None)
            ln = getattr(sender_data, "last_name", None)

            if fn and ln is not None:
                doc["ut"] = fn + " " + ln
            if ln is None:
                doc["ut"] = fn
            else:
                doc["ut"] = ln

        doc["date"] = aslocaltimestr(message.date)
        doc["m"] = message.raw_text
        if doc["m"] is not None:
            hashes = get_hashtags(message.raw_text)
            if hashes:
                doc["hashes"] = hashes

        for chat in chat_list:
            chan_id = chat["chan-id"]
            if abs(chat_data.id) == abs(chan_id):
                doc["operation-id"] = chat["op-id"]


    return doc




async def get_messages(client, es_host, index, watch_list):
    """
    Used to grab all available messages
    """
    text_list = []
    for chat in watch_list:
        try:
            async for message in client.iter_messages(chat["chan-id"]):
                d = await doc_builder(message, client, watch_list)
                if d["m"]:
                    clean = fix_up(d["m"])
                    print(clean)
                    text_list.append(clean)
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
                                if q == False:
                                    print("Duplicate file: " + path)
                            else:
                                await client.download_media(message.media, path)
                    except AttributeError as e:
                        pass  # bad yes, but no error spam.


                try:
                    if message.media.webpage:
                        web_loot = {}
                        web_loot["type"] = "url"
                        web_loot["url"] = message.media.webpage.url
                        web_loot["site"] = message.media.webpage.site_name
                        web_loot["discription"] = message.media.webpage.description
                        web_loot["title"] = message.media.webpage.title
                        web_loot["display_url"] = message.media.webpage.display_url
                        web_loot["source-site"] = "telegram"
                        web_loot["date"] = aslocaltimestr(message.date)
                        try:
                            web_loot["author"] = message.media.webpage.author
                        except KeyError:
                            pass
                        try:
                            web_loot["source"] = d["group"]
                        except KeyError:
                            web_loot["source"] = d["ut"]
                        if web_loot["title"] is None:
                            web_loot["title"] = "None"
                        hash_id = hash_(web_loot["url"] + web_loot["source"])
                        await insert_doc(es_host, loot_index, web_loot, hash_id)
                except AttributeError:
                    pass
            ed = extract_ent(text_list)
            for ent in ed:
                print(ent)
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
    parser.add_argument("-s", "--show", help="Show channel id so you can add them to db", action='store_true')
    parser.add_argument("-q", "--quiet", help="suppress output", action='store_true', default=False)
    args = parser.parse_args()
    global q
    q = args.quiet

    # config setup

    CONFIG = UngiConfig(auto_load(args.config))
    global loot_index
    loot_index = CONFIG.loot
    global media_path
    media_path = CONFIG.telegram_media
    client = TelegramClient(CONFIG.telegram_session , CONFIG.telegram_api_id, CONFIG.telegram_api_hash)
    global local_tz
    local_tz = pytz.timezone(CONFIG.timezone)
    # We are retreiving the list of servers in the watch list
    watch_list = []
    chat_id_list = []

    async with client:

        for chat in list_telegram(CONFIG.db_path):
            chat_watch = {}
            real_id = utils.resolve_id(abs(chat[0]))[0]
            chat_watch["rid"] = real_id
            #Note: this is checking for a prefix of 100.
            if int(str(abs(real_id))[:3]) == 100:
                real_id = int(str(abs(real_id))[3:])
            chat_watch["id"] = real_id
            chat_watch["operation"] = int(chat[2])
            watch_list.append(chat_watch)


        dialogs = await client.get_dialogs()

        channel_list = []
        for chan in dialogs:
            if args.show:
                print(f"{abs(chan.id)}|{chan.title}")
            d = {}
            for chat in watch_list:
                if int(str(abs(chan.id))[:3]) == 100:
                    chan.id = int(str(abs(chan.id))[3:])
                if chan.id == chat["id"]:
                    chat_id_list.append(abs(chan.id))
                    d["op-id"] = chat["operation"]
                    d["chan-id"] = abs(chat['id'])
                    channel_list.append(d)

        if args.show:
            for id in channel_list:
                print(id)

        if args.full:

            shuffle(channel_list)  # randomized
            await get_messages(client, CONFIG.es_host, CONFIG.telegram, channel_list)
            print("done, waiting to avoid timeouts")

        @client.on(events.NewMessage(chats=chat_id_list))
        async def newMessage(event):
            d = await doc_builder(event.message, cli/ent, watch_list)
            await log_message(CONFIG.es_host, CONFIG.telegram, d)
            if media_path:
                try:
                    if event.message.media.photo:
                        try:
                            path = media_path + str(aslocaltimestr(message.date)) + f"_{d['group']}.jpg"
                        except KeyError:
                            path = media_path + \
                                str(aslocaltimestr(message.date)) + ".jpg"
                            if os.path.exists(path):
                                if q == False:
                                    print("Duplicate file: " + path)
                            else:
                                await client.download_media(event.message.media, path)
                except AttributeError as e:
                    pass  # bad yes, but no error spam

            try:
                if event.message.media.webpage:
                    web_loot = {}
                    web_loot["type"] = "url"
                    web_loot["url"] = message.media.webpage.url
                    web_loot["site"] = message.media.webpage.site_name
                    web_loot["discription"] = message.media.webpage.description
                    web_loot["title"] = message.media.webpage.title
                    web_loot["display_url"] = message.media.webpage.display_url
                    web_loot["source_site"] = "telegram"
                    web_loot["date"] = aslocaltimestr(event.message.date)
                    try:
                        web_loot["author"] = message.media.webpage.author
                    except KeyError:
                        pass
                    try:
                        web_loot["source"] = d["group"]
                    except KeyError:
                        web_loot["source"] = d["ut"]
                    if web_loot["title"] is None:
                        web_loot["title"] = "None"
                    hash_id = hash_(web_loot["url"] + web_loot["title"] + web_loot["source"])
                    await insert_doc(CONFIG.es_host, CONFIG.loot, web_loot, hash_id)
            except AttributeError:
                pass



        await client.run_until_disconnected()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
