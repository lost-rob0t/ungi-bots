#!/usr/bin/env python3

import requests
import aiohttp
import asyncio

def create_indice(host, name, settings=None):
    try:
        url = host + '/' +  name
        if settings:
            resp = requests.put(url, json=settings)
            return resp.text
        else:
            resp = requests.put(url)
            return resp.text
    except ConnectionError as e:
        print(e)


async def insert_doc(host, index, doc, id=None):
    if id is None:
        path = host + f"/{index}/_doc/"
        r = requests.post(path, json=doc)
        return r
    else:
        path = host + f"/{index}/_doc/{id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(path, json=doc) as r:
                    return  await r.text()
        except SystemError as e:
            print(e)
