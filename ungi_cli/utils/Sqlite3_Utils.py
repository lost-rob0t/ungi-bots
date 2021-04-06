#!/usr/bin/env python3

import sqlite3

def db_init(path, sql_file):
    """
    used for setup (main.py -i)
    reads in a sql file conatining sql commands to
    setup the sqlite3 database.
    """
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        with open(sql_file, "r", encoding="utf-8") as script_file:
            script_sql = script_file.read()
        cur.executescript(script_sql)
        conn.commit()
    except sqlite3.DatabaseError as e:
        print(e)


def create_operation(path, name, description=None):
    """
    Ops are used as a way to track which entities belong to a
    Mission/Operation. its to prevent all the data from globing together
    """
    try:
        if description is None:
            discription = "No dscription provided"
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("INSERT INTO operations(operation_name, operation_description) VALUES(?,?)", (name, description))
        conn.commit()
        return {"Status": "True"}
    except sqlite3.IntegrityError as duplicate_op:
        return {"Status": "Error Duplicate"}

def add_subreddit(path, subreddit, operation_id):
    """
    Adds a Subbreddit to the database.
    Requires: Subreddit name, db path, operation id
    the reddit bot will select all subreddits from the table and scrape them.
    """
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("""INSERT INTO reddit(subreddit, operation_id) VALUES(?,?)""", (subreddit, operation_id))
        conn.commit()
        return {"Status": "True"}
        conn.close()
    except sqlite3.IntegrityError as e:
        print(e)
        return {"Status": "Error Duplicate"}


def list_ops(path):
    """
    List Operations
    only requires a path to the database
    """
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        ops = cur.execute("SELECT * FROM operations")
        data = ops.fetchall()
        return data
        print(ops.fetchall())
        conn.close()
    except sqlite3.DataError as e:
        print(e)

def get_op_id(path, name):
    """
    gets operation id from name
    """
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        op_name = cur.execute("SELECT operation_id FROM operations WHERE operation_name = ?", (name,))
        return op_name.fetchone()
        conn.close()
    except sqlite3.DataError as e:
        print(e)

def list_subreddits(path):
    """
    list monitored subreddits
    """
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        data = cur.execute("SELECT * FROM reddit")
        return data.fetchall()
        conn.close()
    except sqlite3.DataError as e:
        print(e)
