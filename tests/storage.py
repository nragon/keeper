# -*- coding: utf-8 -*-
"""
    Test storage
    :copyright: © 2018 by Nuno Gonçalves
    :license: MIT, see LICENSE for more details.
"""

from os import environ, getcwd
from os.path import join
from shutil import rmtree
from unittest import TestCase

environ["KEEPER_HOME"] = join(getcwd(), "storage")
from kio import Storage


class TestStorage(TestCase):
    def tearDown(self):
        rmtree(environ["KEEPER_HOME"])

    def test_put_str(self):
        with Storage() as storage:
            storage.put("a", "a")
            self.assertEqual(storage.get("a"), "a")

        with Storage() as storage:
            storage.put("b", "a")

        with Storage() as storage:
            self.assertEqual(storage.get("b"), "a")

    def test_put_int(self):
        with Storage() as storage:
            storage.put("a", 1)
            self.assertEqual(storage.get_int("a"), 1)

        with Storage() as storage:
            storage.put("b", 1)

        with Storage() as storage:
            self.assertEqual(storage.get_int("b"), 1)

    def test_put_float(self):
        with Storage() as storage:
            storage.put("a", 1.1)
            self.assertEqual(storage.get_float("a"), 1.1)

        with Storage() as storage:
            storage.put("b", 1.1)

        with Storage() as storage:
            self.assertEqual(storage.get_float("b"), 1.1)

    def test_inc(self):
        value = 1
        with Storage() as storage:
            value = storage.inc("a", value)
            self.assertEqual(storage.get_float("a"), value)

    def test_inc_multiple(self):
        value = 1
        with Storage() as storage:
            value = storage.inc("a", value, 2)
            self.assertEqual(storage.get_float("a"), value)

    def test_update(self):
        with Storage() as storage:
            storage.put("a", "a")
            self.assertEqual(storage.get("a"), "a")

        with Storage() as storage:
            storage.put("a", "b")

        with Storage() as storage:
            self.assertEqual(storage.get("a"), "b")

    def test_get_not_exists(self):
        with Storage() as storage:
            self.assertEqual(storage.get("c"), None)
