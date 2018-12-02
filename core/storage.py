import sqlite3
from contextlib import closing
from multiprocessing import Manager
from os import makedirs
from os.path import join, exists

from core import constants

lock = Manager().Lock()


class Storage(object):
    INSERT_STATEMENT = "insert or ignore into keystore values (?, ?)"
    UPDATE_STATEMENT = "update keystore set value = ? where changes() = 0 and key = ?"
    SELECT_STATEMENT = "select value from keystore where key = ?"
    GET_ALL = "select key, value from keystore"
    GET_KEYS = "select key from keystore"
    NUMBER_TYPE = (int, float)

    def __init__(self):
        storage_path = join(constants.KEEPER_HOME, "storage")
        if not exists(storage_path):
            makedirs(storage_path)

        storage_path = join(storage_path, "keeper.db")
        with closing(sqlite3.connect(storage_path)) as conn:
            c = conn.cursor()
            c.execute("create table if not exists keystore(key text primary key, value text)")

        self.storage_path = storage_path
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.storage_path)

        return self

    def __exit__(self, type, value, traceback):
        conn = self.conn
        if conn:
            conn.close()
            self.conn = None

    def put(self, key, value):
        if isinstance(value, Storage.NUMBER_TYPE):
            value = str(value)

        cursor = self.conn.cursor()
        with lock:
            cursor.execute(Storage.INSERT_STATEMENT, (key, value))
            cursor.execute(Storage.UPDATE_STATEMENT, (value, key))
            self.conn.commit()

        return value

    def inc(self, key, value, inc_value=1):
        value += inc_value
        cursor = self.conn.cursor()
        with lock:
            cursor.execute(Storage.INSERT_STATEMENT, (key, value))
            cursor.execute(Storage.UPDATE_STATEMENT, (value, key))
            self.conn.commit()

        return value

    def get(self, key):
        cursor = self.conn.cursor()
        result = cursor.execute(Storage.SELECT_STATEMENT, (key,)).fetchone()

        return result[0] if result else None

    def get_int(self, key):
        result = self.get(key)

        return int(result) if result else 0

    def get_float(self, key):
        result = self.get(key)

        return float(result) if result else 0

    def get_all(self):
        return self.conn.cursor().execute(Storage.GET_ALL).fetchall()
