import aiosqlite
from enum import Enum
import os


class Status(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"


class SQLiteDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.images_table_name = 'images'
        self.cascade_table_name = 'cascade'
        self.sense_table_name = 'sense'
        self.nft_table_name = 'nft'
        self.collection_table_name = 'collections'

    async def initialize_db(self):
        if not os.path.exists(self.db_path):
            async with aiosqlite.connect(self.db_path) as db:
                # collection_type is nft or sense
                await db.execute(f'''
                    CREATE TABLE IF NOT EXISTS {self.collection_table_name} (
                        id INTEGER PRIMARY KEY,
                        collection_type TEXT,
                        name TEXT,
                        max_collection_entries INTEGER,
                        collection_item_copy_count INTEGER,
                        list_of_pastelids_of_authorized_contributors TEXT,
                        max_permitted_open_nsfw_score REAL,
                        minimum_similarity_score_to_first_entry_in_collection REAL,
                        no_of_days_to_finalize_collection INTEGER,
                        royalty REAL,
                        green BOOLEAN,
                        status TEXT,
                        req_id TEXT,
                        res_id TEXT,
                        reg_txid TEXT,
                        act_txid TEXT 
                    )
                ''')
                await db.execute(f'''
                    CREATE TABLE IF NOT EXISTS {self.cascade_table_name} (
                        id INTEGER PRIMARY KEY,
                        make_publicly_accessible BOOLEAN,
                        status TEXT,
                        req_id TEXT,
                        res_id TEXT,
                        reg_txid TEXT,
                        act_txid TEXT
                    )
                ''')
                await db.execute(f'''
                    CREATE TABLE IF NOT EXISTS {self.sense_table_name} (
                        id INTEGER PRIMARY KEY,
                        collection_act_txid TEXT, 
                        open_api_group_id TEXT,
                        status TEXT,
                        req_id TEXT,
                        res_id TEXT,
                        reg_txid TEXT,
                        act_txid TEXT, 
                        FOREIGN KEY(collection_act_txid) REFERENCES {self.collection_table_name}(act_txid)
                    )
                ''')
                await db.execute(f'''
                    CREATE TABLE IF NOT EXISTS {self.nft_table_name} (
                        id INTEGER PRIMARY KEY,
                        issued_copies INTEGER,
                        royalty REAL,
                        green BOOLEAN,
                        collection_act_txid TEXT, 
                        open_api_group_id TEXT,
                        make_publicly_accessible BOOLEAN,
                        status TEXT,
                        req_id TEXT,
                        res_id TEXT,
                        reg_txid TEXT,
                        act_txid TEXT, 
                        FOREIGN KEY(collection_act_txid) REFERENCES {self.collection_table_name}(act_txid)
                    )
                ''')
                await db.execute(f'''
                    CREATE TABLE IF NOT EXISTS {self.images_table_name} (
                    id INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    name TEXT,
                    creator_name TEXT,
                    keywords TEXT,
                    series_name TEXT,
                    file_path TEXT,
                    cascade_id INTEGER,
                    sense_id INTEGER,
                    nft_id INTEGER,
                    FOREIGN KEY(cascade_id) REFERENCES {self.cascade_table_name}(id),
                    FOREIGN KEY(sense_id) REFERENCES {self.sense_table_name}(id),
                    FOREIGN KEY(nft_id) REFERENCES {self.nft_table_name}(id)
                    )
                ''')

                await db.commit()

    async def add_image(self, description: str, name: str, file_path: str,
                        creator_name: str = "pastel.network", keywords: str = None, series_name: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"INSERT INTO {self.images_table_name} "
                             f"(description, name, file_path, "
                             f"creator_name, keywords, series_name) "
                             f"VALUES (?, ?, ?, ?, ?, ?)",
                             (description, name, file_path,
                              creator_name, keywords, series_name, ))
            await db.commit()

    async def read_all_images(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(f"SELECT * FROM {self.images_table_name}") as cursor:
                return await cursor.fetchall()

    async def find_image_for_cascade(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(f"SELECT * FROM {self.images_table_name} WHERE cascade_id IS NULL") as cursor:
                return await cursor.fetchone()

    async def find_image_for_sense_or_nft(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(f"SELECT * FROM {self.images_table_name} "
                                  f"WHERE sense_id IS NULL AND nft_id is NULL ") as cursor:
                return await cursor.fetchone()

    async def add_cascade(self, img_id, res_status: str, req_id: str, res_id: str, reg_txid: str, act_txid: str,
                          make_publicly_accessible: bool = True):
        await self._add_ticket_record(self.cascade_table_name, 'cascade_id', img_id,
                                      res_status, req_id, res_id, reg_txid, act_txid,
                                      make_publicly_accessible=make_publicly_accessible)

    async def add_sense(self, img_id, res_status: str, req_id: str, res_id: str, reg_txid: str, act_txid: str,
                        collection_act_txid: str = None, open_api_group_id: str = None):
        await self._add_ticket_record(self.sense_table_name, 'sense_id', img_id,
                                      res_status, req_id, res_id, reg_txid, act_txid,
                                      collection_act_txid=collection_act_txid, open_api_group_id=open_api_group_id)

    async def add_nft(self, img_id, res_status: str, req_id: str, res_id: str, reg_txid: str, act_txid: str,
                      issued_copies: int, royalty: float, green: bool,
                      collection_act_txid: str = None, open_api_group_id: str = None,
                      make_publicly_accessible: bool = True):
        await self._add_ticket_record(self.nft_table_name, 'nft_id', img_id,
                                      res_status, req_id, res_id, reg_txid, act_txid,
                                      issued_copies=issued_copies, royalty=royalty, green=green,
                                      collection_act_txid=collection_act_txid, open_api_group_id=open_api_group_id,
                                      make_publicly_accessible=make_publicly_accessible)

    async def _add_ticket_record(self, table_name: str, img_col_name: str, img_id,
                                 res_status: str, req_id: str, res_id: str, reg_txid: str, act_txid: str,
                                 **extra_fields):
        placeholders = ', '.join(['?'] * (5 + len(extra_fields)))
        field_names = ', '.join(['status', 'req_id', 'res_id', 'reg_txid', 'act_txid'] + list(extra_fields.keys()))
        values = (res_status, req_id, res_id, reg_txid, act_txid) + tuple(extra_fields.values())

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(f"INSERT INTO {table_name} "
                                      f"({field_names}) "
                                      f"VALUES ({placeholders})",
                                      values)
            await db.commit()
            record_id = cursor.lastrowid
            await db.execute(f"UPDATE {self.images_table_name} SET {img_col_name} = ? WHERE id = ?",
                             (record_id, img_id))
            await db.commit()

    async def update_cascade_status(self, ticket_id, status: str, reg_txid: str, act_txid: str):
        await self._update_status(self.cascade_table_name, ticket_id, status, reg_txid, act_txid)

    async def update_sense_status(self, ticket_id, status: str, reg_txid: str, act_txid: str):
        await self._update_status(self.sense_table_name, ticket_id, status, reg_txid, act_txid)

    async def update_nft_status(self, ticket_id, status: str, reg_txid: str, act_txid: str):
        await self._update_status(self.nft_table_name, ticket_id, status, reg_txid, act_txid)

    async def update_collections_status(self, ticket_id, status: str, reg_txid: str, act_txid: str):
        await self._update_status(self.collection_table_name, ticket_id, status, reg_txid, act_txid)

    async def _update_status(self, table_name: str, ticket_id, status: str, reg_txid: str, act_txid: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE {table_name} SET status = ?, reg_txid = ?, act_txid = ? WHERE id = ?",
                             (status, reg_txid, act_txid, ticket_id, ))
            await db.commit()

    async def get_cascade_pending(self):
        return await self._get_pending_tickets(self.cascade_table_name)

    async def get_sense_pending(self):
        return await self._get_pending_tickets(self.sense_table_name)

    async def get_nft_pending(self):
        return await self._get_pending_tickets(self.nft_table_name)

    async def get_collections_pending(self):
        return await self._get_pending_tickets(self.collection_table_name)

    async def _get_pending_tickets(self, table_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(f"SELECT * FROM {table_name} WHERE status != 'SUCCESS'") as cursor:
                return await cursor.fetchall()

    async def get_cascade_counts(self):
        return await self._get_ticket_counts(self.cascade_table_name)

    async def get_sense_counts(self):
        return await self._get_ticket_counts(self.sense_table_name)

    async def get_nft_counts(self):
        return await self._get_ticket_counts(self.nft_table_name)

    async def get_collections_counts(self):
        return await self._get_ticket_counts(self.collection_table_name)

    async def _get_ticket_counts(self, table_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(f"SELECT status, COUNT(*) FROM {table_name} GROUP BY status") as cursor:
                return await cursor.fetchall()
