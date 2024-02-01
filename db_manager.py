import sqlite3
import os


class SQLiteDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.table_name = 'records'
        self.conn = None
        self._initialize_db()

    def _initialize_db(self):
        if not os.path.exists(self.db_path):
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute(f'''
                CREATE TABLE {self.table_name} (
                    id INTEGER PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    file_name TEXT,
                    status TEXT,
                    req_id TEXT,
                    res_id TEXT,
                    txid TEXT
                )
            ''')
        else:
            self.conn = sqlite3.connect(self.db_path)

    def add_record(self, prompt):
        with self.conn:
            self.conn.execute(f"INSERT INTO {self.table_name} (prompt) VALUES (?)", (prompt,))

    def read_records_with_prompt(self):
        with self.conn:
            return self.conn.execute(f"SELECT * FROM {self.table_name} WHERE file_name IS NULL").fetchall()

    def update_record_file_name(self, id, file_name):
        with self.conn:
            self.conn.execute(f"UPDATE {self.table_name} SET file_name = ? WHERE id = ?", (file_name, id))

    def read_records_with_prompt_file_name(self):
        with self.conn:
            return self.conn.execute(f"SELECT * FROM {self.table_name} WHERE file_name IS NOT NULL").fetchall()

    def update_record_status(self, id, status, req_id=None, res_id=None):
        with self.conn:
            self.conn.execute(f'''
                UPDATE {self.table_name} SET status = ?, req_id = ?, res_id = ? WHERE id = ?''',
                (status, req_id, res_id, id))

    def read_records_without_txid(self):
        with self.conn:
            return self.conn.execute(f"SELECT * FROM {self.table_name} WHERE txid IS NULL").fetchall()

    def update_record_txid(self, id, txid):
        with self.conn:
            self.conn.execute(f"UPDATE {self.table_name} SET txid = ? WHERE id = ?", (txid, id))

    def read_records_with_status(self, status):
        with self.conn:
            return self.conn.execute(f"SELECT * FROM {self.table_name} WHERE status = ?", (status,)).fetchall()

# Example Usage
db = SQLiteDB('example.db')
db.add_record("Sample prompt")
print(db.read_records_with_prompt())
db.update_record_file_name(1, "sample_file.txt")
print(db.read_records_with_prompt_file_name())
db.update_record_status(1, "Processed", "req123", "res456")
print(db.read_records_without_txid())
db.update_record_txid(1, "tx789")
print(db.read_records_with_status("Processed"))
