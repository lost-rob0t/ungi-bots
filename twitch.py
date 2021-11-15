#!/usr/bin/env python3

from ungi_utils.Sqlite3_Utils import list_twitch, list_twitch_bots, hash_, get_alert_level
from ungi_utils.Elastic_Wrapper import insert_doc
from ungi_utils.Config import UngiConfig
from twitchio.ext import commands
from argparse import ArgumentParser
from datetime import datetime
from termcolor import colored
from ungi_utils.entity_utils import send_alert

parser = ArgumentParser()
parser.add_argument("-t", "--token", help="OAUTH token")
parser.add_argument("-c", "--client_id", help="client id")
parser.add_argument("-n", "--nickname", help="nickname for the bot")
parser.add_argument("-v", "--verbose", help="be verbose with Information", default=False, action="store_true")
parser.add_argument("--config", help="config for bot", default="app.ini", required=True)
args = parser.parse_args()

CONFIG = UngiConfig(args.config)
channel_list = list_twitch(CONFIG.db_path)
channel_manage = []

for chan in channel_list:
    d = {}
    d["name"] = chan[0]
    d["operation-id"] = chan[1]
    d["alert-level"] = get_alert_level(CONFIG.db_path, chan[1])[0]
    channel_manage.append(d)

class Ungi(commands.Bot):
    def __init__(self):
        print(f"Project: {CONFIG.project_name}")
        print(f"Total Channels: {len(channel_manage)}")
        super().__init__(token=args.token,
                        client_id=args.client_id,
                        nick=args.nickname,
                        prefix="`",
                        initial_channels=[x["name"] for x in channel_manage])

    async def event_ready(self):
        print(colored(f'Bot username: {self.nick}', "green"))


    async def event_message(self, message):

       ## I should do this better
       ## Looks for the current channel in a list of dicts, when it matches
       ## it adds the operation/alert setting.
       for x in channel_manage:
           if x["name"].lower() == message.channel.name.lower():
               if x["operation-id"]:

                   ## Log the message
                   md = {}
                   md["m"] = message.content
                   md["ut"] = message.author.name
                   md["cn"] = message.channel.name
                   md["operation-id"] = x["operation-id"]
                   md["date"] = datetime.now().isoformat()
                   md["hash"] = hash_(md["m"] + md["cn"] + md["date"] + md["ut"])
                   await insert_doc(CONFIG.es_host, CONFIG.twitch, md, id=md["hash"])
                   if 20 >= x["alert-level"]:
                       pass
                   if args.verbose:
                       print(colored(md, "blue"))
                   else:
                    ## this should basicly never happen, unlike discord the chats are loaded from the db and MUST
                    ## Have a operation attached to it, this is just incase
                       print(colored(f"{x['name']} is not being monitored!"), "red")

ungi = Ungi()


ungi.run()
