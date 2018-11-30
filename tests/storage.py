from os import environ, getcwd
from os.path import join
from shutil import rmtree
from unittest import TestCase

environ["KEEPER_HOME"] = join(getcwd(), "storage")
from core import storage


class Storage(TestCase):
    def setUp(self):
        storage.setup()

    def tearDown(self):
        rmtree(environ["KEEPER_HOME"])

    def test_put_str(self):
        with storage.get_connection() as conn:
            storage.put(conn, "a", "a")
            self.assertEqual(storage.get(conn, "a"), "a")

        with storage.get_connection() as conn:
            storage.put(conn, "b", "a")

        with storage.get_connection() as conn:
            self.assertEqual(storage.get(conn, "b"), "a")

    def test_put_int(self):
        with storage.get_connection() as conn:
            storage.put(conn, "a", 1)
            self.assertEqual(storage.get_int(conn, "a"), 1)

        with storage.get_connection() as conn:
            storage.put(conn, "b", 1)

        with storage.get_connection() as conn:
            self.assertEqual(storage.get_int(conn, "b"), 1)

    def test_put_float(self):
        with storage.get_connection() as conn:
            storage.put(conn, "a", 1.1)
            self.assertEqual(storage.get_float(conn, "a"), 1.1)

        with storage.get_connection() as conn:
            storage.put(conn, "b", 1.1)

        with storage.get_connection() as conn:
            self.assertEqual(storage.get_float(conn, "b"), 1.1)

    def test_inc(self):
        value = 1
        with storage.get_connection() as conn:
            value = storage.inc(conn, "a", value)
            self.assertEqual(storage.get_float(conn, "a"), value)

    def test_inc_multiple(self):
        value = 1
        with storage.get_connection() as conn:
            value = storage.inc(conn, "a", value, 2)
            self.assertEqual(storage.get_float(conn, "a"), value)

    def test_update(self):
        with storage.get_connection() as conn:
            storage.put(conn, "a", "a")
            self.assertEqual(storage.get(conn, "a"), "a")

        with storage.get_connection() as conn:
            storage.put(conn, "a", "b")

        with storage.get_connection() as conn:
            self.assertEqual(storage.get(conn, "a"), "b")

    def test_get_not_exists(self):
        with storage.get_connection() as conn:
            self.assertEqual(storage.get(conn, "c"), None)

    def test_get_keys(self):
        with storage.get_connection() as conn:
            storage.put(conn, "a", "a")
            storage.put(conn, "b", "b")
            self.assertEqual(list(storage.get_keys(conn)), ["a", "b"])

    def test_get_all(self):
        with storage.get_connection() as conn:
            storage.put(conn, "a", "a")
            storage.put(conn, "b", "b")
            self.assertEqual(storage.get_all(conn), [("a", "a"), ("b", "b")])
