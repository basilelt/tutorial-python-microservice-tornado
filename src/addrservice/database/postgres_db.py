# Copyright (c) 2020. All rights reserved.

import asyncio
import asyncpg
import json
import uuid
from typing import AsyncIterator, Dict, Tuple

from addrservice.datamodel import AddressEntry
from addrservice.database.addressbook_db import AbstractAddressBookDB


class PostgresAddressBookDB(AbstractAddressBookDB):
    def __init__(self, config: Dict):
        """
        Initialize PostgreSQL database connection with configuration.
        
        Config should include:
        - host: database host
        - port: database port
        - user: database user
        - password: database password
        - database: database name
        """
        self.config = config
        self.pool = None
    
    async def _init_db(self):
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                user=self.config.get('user', 'postgres'),
                password=self.config.get('password', ''),
                database=self.config.get('database', 'addressbook')
            )
            
            # Create table if it doesn't exist
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS addresses (
                        nickname TEXT PRIMARY KEY,
                        data JSONB NOT NULL
                    )
                ''')

    def start(self):
        # Create event loop to initialize database in synchronous context
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._init_db())
    
    def stop(self):
        # Close the connection pool
        if self.pool:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.pool.close())
            self.pool = None
    
    async def create_address(
        self,
        addr: AddressEntry,
        nickname: str = None
    ) -> str:
        if nickname is None:
            nickname = uuid.uuid4().hex
        
        # Ensure pool is initialized
        await self._init_db()
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    'INSERT INTO addresses (nickname, data) VALUES ($1, $2)',
                    nickname, json.dumps(addr.to_api_dm())
                )
            except asyncpg.exceptions.UniqueViolationError:
                raise KeyError(f'{nickname} already exists')
        
        return nickname
    
    async def read_address(self, nickname: str) -> AddressEntry:
        # Ensure pool is initialized
        await self._init_db()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT data FROM addresses WHERE nickname = $1',
                nickname
            )
            
            if row is None:
                raise KeyError(nickname)
            
            return AddressEntry.from_api_dm(json.loads(row['data']))
    
    async def update_address(self, nickname: str, addr: AddressEntry) -> None:
        # Ensure pool is initialized
        await self._init_db()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                'UPDATE addresses SET data = $1 WHERE nickname = $2',
                json.dumps(addr.to_api_dm()), nickname
            )
            
            if result == "UPDATE 0":  # No rows updated
                raise KeyError(nickname)
    
    async def delete_address(self, nickname: str) -> None:
        # Ensure pool is initialized
        await self._init_db()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                'DELETE FROM addresses WHERE nickname = $1',
                nickname
            )
            
            if result == "DELETE 0":  # No rows deleted
                raise KeyError(nickname)
    
    async def read_all_addresses(self) -> AsyncIterator[Tuple[str, AddressEntry]]:
        # Ensure pool is initialized
        await self._init_db()
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('SELECT nickname, data FROM addresses')
        
        for row in rows:
            yield (row['nickname'], 
                  AddressEntry.from_api_dm(json.loads(row['data'])))
