# -*- coding: utf-8 -*-
"""
    Provides base access to backend storage
    :copyright: © 2018 by Nuno Gonçalves
    :license: MIT, see LICENSE for more details.
"""

from sqlite3 import connect
from contextlib import closing, contextmanager
from multiprocessing import Manager
from os import makedirs
from os.path import join, exists
from core import KEEPER_HOME

# this should be instantiate by keeper manager
# and used by runtime managers
lock = Manager().Lock()


class Storage(object):
    """
    Holds connection and basic methods for accessing storage
    """
    # base statements
    INSERT_STATEMENT = "insert or ignore into keystore(value, key) values(?, ?)"
    UPDATE_STATEMENT = "update keystore set value = ? where changes() = 0 and key = ?"
    SELECT_STATEMENT = "select value from keystore where key = ?"
    GET_ALL = "select key, value from keystore"
    GET_KEYS = "select key from keystore"
    NUMBER_TYPE = (int, float)

    def __init__(self):
        """
        initializes storage object
        """

        # creates storage directory if not present
        storage_path = join(KEEPER_HOME, "storage")
        if not exists(storage_path):
            makedirs(storage_path)
        # create database and kv table
        storage_path = join(storage_path, "keeper.db")
        with closing(connect(storage_path)) as conn, lock:
            conn.cursor().execute("create table if not exists keystore(key text primary key, value text)")

        self.storage_path = storage_path
        self.conn = None

    def __enter__(self):
        """
        create initial connection when entering context
        :return: Storage object
        """

        conn = connect(self.storage_path)
        conn.execute("pragma journal_mode=wal")
        self.conn = conn

        return self

    # noinspection PyShadowingBuiltins
    def __exit__(self, type, value, traceback):
        """
        closes connection when exiting context
        :param type:
        :param value:
        :param traceback:
        """

        try:
            self.conn.close()
        except Exception:
            pass

        self.conn = None

    def put(self, key, value):
        """
        inserts/updates a value for a given key
        :param key: Key
        :param value: Value
        :return: initial value
        """

        initial_value = value
        # converts numeric type into string
        if isinstance(value, Storage.NUMBER_TYPE):
            value = str(value)

        # upsert statement
        binds = (value, key)
        with lock, self.transaction(self.conn) as cursor:
            cursor.execute(Storage.INSERT_STATEMENT, binds)
            cursor.execute(Storage.UPDATE_STATEMENT, binds)

        return initial_value

    def inc(self, key, value, inc_value=1):
        """
        increments a value for a given key
        :param key: Key
        :param value: Value
        :param inc_value: units to increment, default 1
        :return: returns value already incremented
        """

        value += inc_value
        binds = (value, key)
        with lock, self.transaction(self.conn) as cursor:
            cursor.execute(Storage.INSERT_STATEMENT, binds)
            cursor.execute(Storage.UPDATE_STATEMENT, binds)

        return value

    def get(self, key):
        """
        return the key value
        :param key: key
        :return: key value
        """

        result = self.conn.cursor().execute(Storage.SELECT_STATEMENT, (key,)).fetchone()

        return result[0] if result else None

    def get_int(self, key):
        """
        return the key value as int value
        :param key: key
        :return: key value
        """

        result = self.get(key)

        return int(result) if result else 0

    def get_float(self, key):
        """
        return the key value as float value
        :param key: key
        :return: key value
        """

        result = self.get(key)

        return float(result) if result else 0

    @contextmanager
    def transaction(self, conn):
        """
        base context to execute transactions
        :param conn: connection
        """
        conn.execute("begin")
        try:
            yield conn.cursor()
        except:
            conn.rollback()
        else:
            conn.commit()
