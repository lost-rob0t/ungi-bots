#!/usr/bin/env python3

from os import environ
import asyncpraw
from ungi_utils.Config import auto_load, UngiConfig
from ungi_utils.Elastic_Wrapper import insert_doc
from ungi_utils.Sqlite3_Utils import hash_
import sqlite3
import asyncio
import datetime
import argparse
from random import shuffle  # used for randomizing the subreddit list
# config setup


# Used to return all the subreddits with their operation id


def list_subreddits(path):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    data = cur.execute("SELECT subreddit, operation_id FROM reddit;")
    return data.fetchall()


async def insert_es(es_host, es_index, data, data_type=None):
    if data_type == "comment":
        hash_id = hash_(str(data["body"]) +
                           str(data["date"]) +
                           str(data["author"]))
    if data_type == "post":
        hash_id = hash_(str(["post-title"]) +
                           str(data["date"]) +
                           str(data["op"]) +
                           str(data["subreddit"]))
    await insert_doc(es_host, es_index, data, hash_id)


async def scrape(reddit_obj, db_path, es_host, es_index, limit):
    subs = list_subreddits(db_path)
    shuffle(subs)
    for sub in subs:
        print(sub)
        sub, operation_id = sub
        subreddit = await reddit_obj.subreddit(sub.rstrip())
        print(f'Scraping: {sub}')
        async for submission in subreddit.new(limit=limit):
            rd = {}
            rd["post-title"] = str(submission.title)
            rd["op"] = str(submission.author)
            if submission.is_self:  # a self post is a text post
                rd["text"] = str(submission.selftext)

            if submission.url:  # Check if the post has a link
                rd["link"] = str(submission.url)
            rd["date"] = str(
                datetime.datetime.fromtimestamp(
                    submission.created_utc).isoformat())
            rd["subreddit"] = str(submission.subreddit)
            rd["operation-id"] = operation_id
            await insert_es(es_host, es_index, rd, "post")

            # I got this code snippet from the asyncpraw docs
            # It should produce all comments from a submission
            comments = await submission.comments()
            await comments.replace_more(limit=0)
            comment_queue = comments[:]  # Seed with top-level
            while comment_queue:
                comment = comment_queue.pop(0)
                comment_dict = {}
                comment_dict["author"] = str(comment.author)
                comment_dict["body"] = str(comment.body)
                comment_dict["date"] = str(
                    datetime.datetime.fromtimestamp(
                        comment.created_utc).isoformat())
                comment_dict["submission"] = str(comment.submission)
                comment_dict["subreddit"] = str(comment.subreddit)
                comment_dict["parent"] = str(comment.parent_id)
                comment_dict["id"] = str(comment.id)
                comment_dict["operation-id"] = operation_id
                await insert_es(es_host, es_index, comment_dict, "comment")
                comment_queue.extend(comment.replies)

    await reddit_obj.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--limit",
        help="max number of post to pull at a time",
        type=int)
    parser.add_argument(
        "-f",
        "--full",
        help="Grab every public submission available",
        action="store_true")
    parser.add_argument(
        "-c",
        "--config",
        help="Path to config"
    )
    args = parser.parse_args()


    CONFIG = UngiConfig(auto_load(args.config))
    # Setting up the reddit instance

    reddit = asyncpraw.Reddit(
        client_id=CONFIG.reddit_client_id,
        client_secret=CONFIG.reddit_client_secret,
        username=CONFIG.reddit_client_username,
        password=CONFIG.reddit_client_password,
        user_agent=CONFIG.reddit_client_user_agent)


    if args.full:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(scrape(reddit, CONFIG.db_path, CONFIG.es_host, CONFIG.reddit, None))
        loop.run_until_complete(reddit.close())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(scrape(reddit, CONFIG.db_path, CONFIG.es_host, CONFIG.reddit, args.limit))
        loop.run_until_complete(reddit.close())

if __name__ == "__main__":
    main()
