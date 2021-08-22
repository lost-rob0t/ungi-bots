#!/usr/bin/env python3

#!/usr/bin/env python3
from ungi_utils.Elastic_Wrapper import insert_doc
from ungi_utils.Sqlite3_Utils import hash_, list_telegram, get_alert_level, list_targets, get_words
from ungi_utils.Config import auto_load, UngiConfig
from ungi_utils.entity_utils import get_hashtags, send_alert
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
import re
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
        try:
            sender_data = await message.get_sender()
            chat_data = await message.get_chat()
        except AttributeError:
            pass #not sure what causes this?
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
                doc["operation-id"] = chat["operation-id"]


    return doc




async def get_messages(client, es_host, index, watch_list):
    print("grabbing messages")
    for chat in watch_list:
        try:
            print(chat)
            async for message in client.iter_messages(chat["chan-id"]):
                d = await doc_builder(message, client, watch_list)
                if d["m"]:
                    await log_message(es_host, index, d)

                try:
                    if message.media.photo:
                        if store_media:
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
                except AttributeError:
                    pass #no error spam

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
        except ChannelPrivateError:
            print(f"{chat} is private")

        print("done, waiting to avoid timeouts")
        sleep(1)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to config file")
    parser.add_argument("--appid", help="app id")
    parser.add_argument("--phone", help="account phone number")
    parser.add_argument("--apphash", help="app hash")
    parser.add_argument(
        "-f",
        "--full",
        help="Get complete Chat Histories",
        action="store_true")
    parser.add_argument("-s", "--show", help="Show channel id so you can add them to db", action='store_true')
    parser.add_argument("-q", "--quiet", help="suppress output", action='store_true', default=False)
    parser.add_argument("-d", "--dump", help="dump channel ids to a file")
    args = parser.parse_args()
    global q
    global loot_index
    global local_tz
    global media_path
    global store_media
    q = args.quiet

    # config setup

    CONFIG = UngiConfig(auto_load(args.config))
    print("Ungi Config: ", CONFIG.config_path)
    print("Telegram app id: ", args.appid)
    print("Telegram app hash: ", args.apphash)
    print("telegram Phone number: ", args.phone)
    loot_index = CONFIG.loot
    store_media = bool(CONFIG.telegram_store_media)
    media_path = CONFIG.telegram_media
    client = TelegramClient(CONFIG.session_dir + "/" + args.apphash + ".session", args.appid, args.apphash)
    local_tz = pytz.timezone(CONFIG.timezone)
    # We are retreiving the list of servers in the watch list
    watch_list = []
    chat_id_list = []
    target_list = []
    word_list = []
    async with client:

        for chat in list_telegram(CONFIG.db_path):
            chat_watch = {}
            real_id = utils.resolve_id(abs(chat[0]))[0]
            chat_watch["rid"] = real_id
            
            #Note: this is checking for a prefix of 100.
            if int(str(abs(real_id))[:3]) == 100:
                real_id = int(str(abs(real_id))[3:])
            chat_watch["chan-id"] = real_id
            chat_watch["operation-id"] = int(chat[2])
            chat_watch["alert-level"] = get_alert_level(CONFIG.db_path, chat[2])[0]
            watch_list.append(chat_watch)


        for word in get_words(CONFIG.db_path):
            word_d = {}
            word_d["word"] = word[0]
            word_d["operation-id"] = word[1]

        for target in list_targets(CONFIG.db_path):
            target_d = {}
            target_d["target"] = target[0]
            target_d["operation-id"] = target[2]

        dialogs = await client.get_dialogs()

        channel_list = []
        file_output = []
        for chan in dialogs:
            file_output.append(f"{abs(chan.id)}|{chan.title}")
            if args.show:
                print(f"{abs(chan.id)}|{chan.title}")
            d = {}
            for chat in watch_list:
                if int(str(abs(chan.id))[:3]) == 100:
                    chan.id = int(str(abs(chan.id))[3:])
                if chan.id == chat["chan-id"]:
                    chat_id_list.append(abs(chan.id))
                    
                    # this is kind of retarded
                    d["operation-id"] = chat["operation-id"]
                    d["chan-id"] = abs(chat['chan-id'])
                    channel_list.append(d)

        if args.dump:
            print("writing to file: ", args.dump)
            with open(args.dump, "a") as file_out:
                for line in file_output:
                    file_out.write(line)


        @client.on(events.NewMessage(chats=chat_id_list))
        async def newMessage(event):
            d = await doc_builder(event.message, client, watch_list)
            await log_message(CONFIG.es_host, CONFIG.telegram, d)
            min_level = 0
            print(d)
            
            # We loop over hte list of operations. if the doc has the operation id and the watch list has one
            # we then set the corsponding alert level
            for chat in watch_list:
                if d["operation-id"] == chat["operation-id"]:
                    min_level = chat["alert-level"]
            try:
                if 20 >= min_level and event.message.media is None:
                    if d["ut"]:
                        send_alert(d["m"], d["ut"], d["group"], "new_message", str(f"{CONFIG.server_host}:{CONFIG.server_port}/alert"))
                    else:
                        send_alert(d["m"], d["group"], d["group"], "new_message", str(f"{CONFIG.server_host}:{CONFIG.server_port}/alert"))
            except KeyError:
                    pass
            except AttributeError:
                pass
            try:
                for target in target_list:
                    if target["target"] == d["ut"]:
                        if 75 >= min_level:
                            send_alert("New image", d["ut"], d["group"].rstrip(), "target", str(f"{CONFIG.server_host}:{CONFIG.server_port}/alert"))
            except KeyError:
                pass
            for word in word_list:
                try:
                    r = re.match(word, d["m"])
                    if r:
                        source = d["group"] + " | " + r
                        if 85>= min_level:
                            send_alert(d["m"], d["ut"], source, "watch_word", str(f"{CONFIG.server_host}:{CONFIG.server_port}/alert"))
                except KeyError:
                    pass

            try:
                if event.message.photo:
                    if store_media:
                        try:
                            path = media_path + str(aslocaltimestr(event.message.date)) + f"_{d['group']}.jpg"
                            send_alert(d["m"], d["ut"], d["group"], "image", str(f"{CONFIG.server_host}:{CONFIG.server_port}/alert"), path)
                            if os.path.exists(path):
                                if q == False:
                                    print("Duplicate file: " + path)
                            else:
                                await client.download_media(event.message.media, path)
                                if 20 >= min_level:
                                    if d["ut"]:
                                        send_alert(d["m"], d["ut"], d["group"], "image", str(f"{CONFIG.server_host}:{CONFIG.server_port}/alert"), path)
                                    else:
                                        send_alert(d["m"], d["group"], d["group"], "image", str(f"{CONFIG.server_host}:{CONFIG.server_port}/alert"), path)
                        except KeyError:
                            pass
            except AttributeError:
                pass #no error spam

            try:
                if event.message.media.webpage:
                    web_loot = {}
                    web_loot["type"] = "url"
                    web_loot["url"] = event.message.media.webpage.url
                    web_loot["site"] = event.message.media.webpage.site_name
                    web_loot["discription"] = event.message.media.webpage.description
                    web_loot["title"] = event.message.media.webpage.title
                    web_loot["display_url"] = event.message.media.webpage.display_url
                    web_loot["source_site"] = "telegram"
                    web_loot["date"] = aslocaltimestr(event.message.date)
                    try:
                        web_loot["author"] = event.message.media.webpage.author
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
                    
                    if 20 >= min_level:
                        send_alert(web_loot["url"], d["ut"], d["group"], "new_message", str(f"{CONFIG.server_host}:{CONFIG.server_port}/alert"))
            except AttributeError:
                pass
            if args.full:
                shuffle(channel_list)  # randomized
                await get_messages(client, CONFIG.es_host, CONFIG.telegram, channel_list)
                print("done, waiting to avoid timeouts")
        await client.run_until_disconnected()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
