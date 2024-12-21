import sqlite3
import typing as tp
from enum import Enum

class Errors(Enum):
    INTEGRITY_ERROR = "integrityError"

class ClientsDB:
    """
    Класс для работы с локальной базой данных (SQLite).
    Осуществляет:
    - Создание таблицы t_client
    - Добавление пользователя
    - Получение Google Calendar ID
    - Получение Todoist токена
    - Обновление идентификаторов
    - Удаление пользователя
    """

    def __init__(self, db_name: str = "clients.db") -> None:
        """
        Инициализация базы данных:
        1) Открываем/создаём файл db_name
        2) Вызываем create_tables() для гарантированного наличия нужных таблиц
        """
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self) -> None:
        """
        Создаёт таблицу t_client, если её ещё нет.

        Структура:
        - telegram_id: уникальный ID пользователя (TEXT)
        - google_calendar_id: хранит идентификатор календаря
        - todoist_token: хранит токен Todoist
        """
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

        Args:
            telegram_id (str): Уникальный Telegram ID пользователя.
            google_calendar_id (str): Идентификатор календаря Google.
            todoist_token (str): Токен доступа к Todoist.

        Returns:
            int or Errors.INTEGRITY_ERROR: ID записи, либо Errors.INTEGRITY_ERROR при конфликте, либо Exception.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO t_client (telegram_id, google_calendar_id, todoist_token) VALUES (?, ?, ?)',
                           (telegram_id, google_calendar_id, todoist_token))
        except sqlite3.IntegrityError:
            return Errors.INTEGRITY_ERROR
        except Exception as e:
            return e
        self.conn.commit()
        client_id = cursor.lastrowid
        cursor.close()
        return client_id

    def get_calendar_id(self, telegram_id: str) -> tp.Optional[str]:
        """
        Получает Google Calendar ID по Telegram ID.

        Args:
            telegram_id (str): Идентификатор пользователя в Telegram.

        Returns:
            str или None: Значение google_calendar_id из БД, если есть, иначе None.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT google_calendar_id
            FROM t_client
            WHERE telegram_id = ?
        ''', (telegram_id,))
        result = cursor.fetchone()
        cursor.close()
        return (result[0] if result else None)

    def get_todoist_token(self, telegram_id: str) -> tp.Optional[str]:
        """
        Получает Todoist токен по Telegram ID.

        Args:
            telegram_id (str): Идентификатор пользователя в Telegram.

        Returns:
            str или None: Значение todoist_token из БД, если есть, иначе None.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT todoist_token
            FROM t_client
            WHERE telegram_id = ?
        ''', (telegram_id,))
        result = cursor.fetchone()
        cursor.close()
        return (result[0] if result else None)

    def delete_client(self, telegram_id: str):
        """
        Удаляет клиента из базы данных по Telegram ID.

        Args:
            telegram_id (str): Идентификатор пользователя в Telegram.
        """
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM t_client WHERE telegram_id = ?', (telegram_id,))
        self.conn.commit()
        cursor.close()

    def update_calendar_id(self, telegram_id, new_calendar_id):
        """
        Обновляет Google Calendar ID в записи пользователя.

        Args:
            telegram_id (str): Telegram ID пользователя.
            new_calendar_id (str): Новый идентификатор календаря.
        Returns:
            bool: True, если обновили хотя бы одну строку, False иначе.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE t_client SET google_calendar_id = ? WHERE telegram_id = ?",
                           (new_calendar_id, telegram_id))
            self.conn.commit()
            updated_rows = cursor.rowcount
            cursor.close()
            return updated_rows > 0
        except Exception:
            return False

    def update_todoist_token(self, telegram_id, new_todoist_token):
        """
        Обновляет Todoist токен в записи пользователя.

        Args:
            telegram_id (str): Telegram ID пользователя.
            new_todoist_token (str): Новый Todoist токен.

        Returns:
            bool: True, если обновили хотя бы одну строку, False иначе.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE t_client SET todoist_token = ? WHERE telegram_id = ?",
                           (new_todoist_token, telegram_id))
            self.conn.commit()
            updated_rows = cursor.rowcount
            cursor.close()
            return updated_rows > 0
        except Exception:
            return False