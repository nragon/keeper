import sqlite3
from multiprocessing import Manager
from os import makedirs
from os.path import join, exists

from core import common

INSERT_STATEMENT = "insert or ignore into keystore values (?, ?)"
UPDATE_STATEMENT = "update keystore set value = ? where changes() = 0 and key = ?"
SELECT_STATEMENT = "select value from keystore where key = ?"
GET_ALL = "select key, value from keystore"
GET_KEYS = "select key from keystore"
NUMBER_TYPE = (int, float)

lock = Manager().Lock()


def setup():
    storage_path = join(common.KEEPER_HOME, "storage")
    if not exists(storage_path):
        makedirs(storage_path)

    with sqlite3.connect(join(storage_path, "vision.db")) as conn:
        c = conn.cursor()
        c.execute("create table if not exists keystore(key text primary key, value text)")

    return conn


def get_connection():
    return sqlite3.connect(join(common.KEEPER_HOME, "storage", "vision.db"))


def put(conn, key, value):
    if isinstance(value, NUMBER_TYPE):
        value = str(value)

    cursor = conn.cursor()
    with lock:
        cursor.execute(INSERT_STATEMENT, (key, value))
        cursor.execute(UPDATE_STATEMENT, (value, key))
        conn.commit()

    return value


def inc(conn, key, value, inc_value=1):
    value += inc_value
    cursor = conn.cursor()
    with lock:
        cursor.execute(INSERT_STATEMENT, (key, value))
        cursor.execute(UPDATE_STATEMENT, (value, key))
        conn.commit()

    return value


def get(conn, key):
    cursor = conn.cursor()
    result = cursor.execute(SELECT_STATEMENT, (key,)).fetchone()

    return result[0] if result else None


def get_int(conn, key):
    result = get(conn, key)

    return int(result) if result else None


def get_float(conn, key):
    result = get(conn, key)

    return float(result) if result else None


def get_keys(conn):
    cursor = conn.cursor()
    result = cursor.execute(GET_KEYS).fetchall()

    return map(map_keys, result) if result else None


def map_keys(key):
    return key[0]


def get_all(conn):
    cursor = conn.cursor()

    return cursor.execute(GET_ALL).fetchall()
