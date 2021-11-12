#!/usr/bin/env python3

from ungi_utils.Config import UngiConfig
from ungi_utils.Sqlite3_Utils import list_telegram_bots, list_discord_bots
import argparse
import subprocess as sub
import concurrent.futures
import os
from time import sleep


def run_telegram(db_path):
    bot_list = list_telegram_bots(db_path)

    # if there is no session file then we need to login, this is an interactive process
    if args.setup:
        for bot in bot_list:
            try:
                print("10 Minute timeout, hit ctr-c when done")
                sub.Popen(f"python3 telegram.py --appid {bot[1]} --apphash {bot[0]} -c {args.config} --phone {bot[2]} -s", shell=True)
                sleep(500)
            except KeyboardInterrupt:
                print("Setting up next account")
                continue
    else:
        print(f"Running {len(bot_list)} telegram accounts")
        if args.dump:
            telegram_bots = [sub.Popen(f"python3 telegram.py --appid {bot[1]} --apphash {bot[0]} -c {args.config} --phone {bot[2]} --dump {args.dump} -s", shell=True) for bot in bot_list]
            exit()
        else:
            telegram_bots = [sub.Popen(f"python3 telegram.py --appid {bot[1]} --apphash {bot[0]} -c {args.config} --phone {bot[2]} -s", shell=True) for bot in bot_list]
        i = 1


def run_discord(db_path):
    bot_list = list_discord_bots(db_path)
    discord_bots = [sub.Popen(f"python3 discord_logger.py -t {bot[0]} -m 2000 --connection {CONFIG.es_host}", shell=True) for bot in bot_list]


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="path to config")
    parser.add_argument("-f", "--full", help="grab everything from chats")
    parser.add_argument("-s", "--setup", help="run bots in setup mode, press ctr-c to cycle through accounts", action="store_true")
    parser.add_argument("--dump", help="Dump telegram channel ids to a text file")
    args = parser.parse_args()
    global CONFIG
    print(args.dump)
    CONFIG = UngiConfig(args.config)
    if args.setup:
        run_telegram(CONFIG.db_path)
        exit(0)
    if CONFIG.use_telegram:
        print("Starting Telegram bots")
        run_telegram(CONFIG.db_path)
    if CONFIG.use_discord:
        print("Starting Discord bots")
        run_discord(CONFIG.db_path)


main()
