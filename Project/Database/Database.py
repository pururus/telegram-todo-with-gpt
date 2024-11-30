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
                        notion_id TEXT NOT NULL
                    )
                ''')
        
        self.conn.commit()


    def add_client(self, telegram_id: str, google_calendar_id: str, notion_id: str) -> int:
        """
        Добавляет клиента в таблицу t_client.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO t_client (telegram_id, google_calendar_id, notion_id) VALUES (?, ?, ?)', (telegram_id, google_calendar_id, notion_id))
        except sqlite3.IntegrityError:
           return Errors.INTEGRITY_ERROR
        except Exception as e:
            return e
        self.conn.commit()
        client_id = cursor.lastrowid
        cursor.close()
        return client_id
    
    def get_calendar_id(self, telegram_id: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute('''
                       SELECT clients.google_calendar_id
                       FROM t_client clients
                       WHERE clients.telegram_id = ?
                    ''', (telegram_id, ))
        calendar_id = cursor.fetchone()
        cursor.close()
        return calendar_id

    def get_notion_id(self, telegram_id: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute('''
                       SELECT clients.notion_id
                       FROM t_client clients
                       WHERE clients.telegram_id = ?
                    ''', (telegram_id, ))
        notion_id = cursor.fetchone()
        cursor.close()
        return notion_id
