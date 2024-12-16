
import sqlite3
import typing as tp
from enum import Enum

class Errors(Enum):
    INTEGRITY_ERROR = "integrityError"

class ClientsDB:
    def __init__(self, db_name: str = "clients.db") -> None:
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self) -> None:
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS t_client (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT UNIQUE NOT NULL,
                google_calendar_id TEXT NOT NULL,
                todoist_token TEXT NOT NULL
            )
        ''')

        self.conn.commit()

    def add_client(self, telegram_id: str, google_calendar_id: str, todoist_token: str) -> int:
        """
        Добавляет клиента в таблицу t_client.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO t_client (telegram_id, google_calendar_id, todoist_token) VALUES (?, ?, ?)', (telegram_id, google_calendar_id, todoist_token))
        except sqlite3.IntegrityError:
            return Errors.INTEGRITY_ERROR
        except Exception as e:
            return e
        self.conn.commit()
        client_id = cursor.lastrowid
        cursor.close()
        return client_id

    def get_calendar_id(self, telegram_id: str) -> tp.Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT google_calendar_id
            FROM t_client
            WHERE telegram_id = ?
        ''', (telegram_id,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def get_todoist_token(self, telegram_id: str) -> tp.Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT todoist_token
            FROM t_client
            WHERE telegram_id = ?
        ''', (telegram_id,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def delete_client(self, telegram_id: str):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM t_client WHERE telegram_id = ?', (telegram_id,))
        self.conn.commit()
        cursor.close()

    def update_calendar_id(self, telegram_id, new_calendar_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE t_client SET calendar_id = ? WHERE telegram_id = ?", (new_calendar_id, telegram_id))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            return False

    def update_todoist_token(self, telegram_id, new_todoist_token):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE t_client SET todoist_token = ? WHERE telegram_id = ?",
                           (new_todoist_token, telegram_id))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            return False