#!/usr/bin/env python3

import requests
import aiohttp
import asyncio
import json
def create_indice(host, name, settings=None):
    try:
        url = host + '/' +  name
        if settings:
            resp = requests.put(url, json=settings)
            return resp.text
        else:
            resp = requests.put(url)
            return resp.json()
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
        except Exception as e:
            print(e)

async def search(host, query, size=0, index=None):
    if index:
        path = host + f"/{index}/_search?size={size}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(path, json=query) as r:
                    data = await r.json()
                    return data
        except ConnectionError as e:
            print(e)
    else:
        path = host + f"/_search?size={size}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(path, json=query) as r:
                    data = await r.json()
                    return data
        except ConnectionError as e:
            print(e)
