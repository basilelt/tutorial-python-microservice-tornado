# Copyright (c) 2020. All rights reserved.

import asynctest  # type: ignore
from io import StringIO
import unittest
import yaml
import os

from addrservice.database.addressbook_db import AbstractAddressBookDB
from addrservice.database.postgres_db import PostgresAddressBookDB
from addrservice.database.db_engines import create_addressbook_db
from addrservice.datamodel import AddressEntry

from tests.unit.addressbook_db_test import AbstractAddressBookDBTestCase
from data import address_data_suite


class PostgresAddressBookDBTest(unittest.TestCase):
    def read_config(self, txt: str):
        with StringIO(txt) as f:
            cfg = yaml.load(f.read(), Loader=yaml.SafeLoader)
        return cfg

    @unittest.skipIf('CI' in os.environ, "Skipping PostgreSQL tests in CI environment")
    def test_postgres_db_config(self):
        cfg = self.read_config('''
addr-db:
  postgres:
    host: localhost
    port: 5432
    user: postgres
    password: postgres
    database: addressbook
        ''')

        self.assertIn('postgres', cfg['addr-db'])
        db = create_addressbook_db(cfg['addr-db'])
        self.assertEqual(type(db), PostgresAddressBookDB)


@unittest.skipIf('CI' in os.environ, "Skipping PostgreSQL tests in CI environment")
class PostgresAddressBookDBIntegrationTest(
    AbstractAddressBookDBTestCase,
    asynctest.TestCase
):
    def make_addr_db(self) -> AbstractAddressBookDB:
        self.pg_config = {
            'host': os.environ.get('PG_HOST', 'localhost'),
            'port': int(os.environ.get('PG_PORT', 5432)),
            'user': os.environ.get('PG_USER', 'postgres'),
            'password': os.environ.get('PG_PASSWORD', 'postgres'),
            'database': os.environ.get('PG_DATABASE', 'addressbook_test')
        }
        self.pg_db = PostgresAddressBookDB(self.pg_config)
        self.pg_db.start()
        return self.pg_db

    def addr_count(self) -> int:
        # This is approximate but works for tests
        count = 0
        async def count_addresses():
            nonlocal count
            async for _ in self.pg_db.read_all_addresses():
                count += 1
        
        loop = asynctest.asyncio.get_event_loop()
        loop.run_until_complete(count_addresses())
        return count

    def tearDown(self):
        self.pg_db.stop()
        super().tearDown()


if __name__ == '__main__':
    unittest.main()
