import requests
import base64
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from Project.Query import Query
from Project.Request import Request, RequestType
from Project.GPT.credentials import cal_credentials

import logging

logging.captureWarnings(True)

class GPT:
    _token = None
    _url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    def get_token(self, auth_token, scope='GIGACHAT_API_PERS'):
        """
        Получение токена для авторизации в API.
        """
        rq_uid = str(uuid.uuid4())
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': rq_uid,
            'Authorization': f'Basic {auth_token}'
        }
        payload = {
            'scope': scope
        }

        try:
            response = requests.post(url, headers=headers, data=payload, verify=False)
            if response.status_code == 200:
                return response.json().get('access_token', None)
            else:
                raise Exception(f"Failed to fetch token: {response.text}")
        except requests.RequestException as e:
            raise Exception(f"Ошибка получения токена: {str(e)}")

    def check_token(self):
        """
        Проверяет наличие токена, если его нет, запрашивает новый.
        """
        encoded_credentials = base64.b64encode(cal_credentials.encode('utf-8')).decode('utf-8')

        if self._token is None:
            self._token = self.get_token(encoded_credentials)
            if not self._token:
                raise Exception("Не удалось получить токен.")

    def request(self, message: str, max_tokens: int = 50, temp=1) -> requests.Response:
        """
        Выполняет запрос к API GigaChat.
        """
        self.check_token()  # Убедимся, что токен валиден

        payload = json.dumps({
            "model": "GigaChat",
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ],
            "stream": False,
            "max_tokens": max_tokens,
            "temperature": temp  # Исправлено
        })

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self._token}'
        }

        try:
            response = requests.post(self._url, headers=headers, data=payload, verify=False)
            response.raise_for_status()  # Проверка HTTP-статуса
            return response
        except requests.RequestException as e:
            raise Exception(f"Ошибка запроса: {str(e)}")

    def get_type(self, content: Query) -> RequestType:
        """
        Определяет тип запроса: событие (event), задача (task), или неизвестный (else).
        """
        self.check_token()

        message = f'''Пользователь отправил сообщение "{content.content}". Определи тип: 'event', 'task' или 'else'.'''

        ans = (self.request(message, 100).json()['choices'][0]['message']['content']).lower()

        if "event" in ans:
            return RequestType.EVENT
        elif "task" in ans:
            return RequestType.GOAL
        else:
            return RequestType.ELSE

    def get_event_content(self, content: Query) -> str:
        """
        Извлекает название события из сообщения пользователя.
        """
        self.check_token()

        message = f'''Определи название события из сообщения "{content.content}".'''

        return self.request(message, 10).json()['choices'][0]['message']['content']

    def get_task_content(self, content: Query) -> str:
        """
        Извлекает формулировку задачи из сообщения пользователя.
        """
        self.check_token()

        message = f'''Определи формулировку задачи из сообщения "{content.content}".'''

        return self.request(message, 15).json()['choices'][0]['message']['content']

    def check_date(self, date: str) -> bool:
        """
        Проверяет корректность формата даты.
        """
        return date[-1] == "T" or date.count("T") == 0

    def makefull(self, time: str) -> str:
        """
        Преобразует время в полный формат.
        """
        time = time.replace(";", '')
        if time.count(":") == 0:
            time += ":00:00"
        elif time.count(":") == 1:
            time += ":00"
        time += "+03:00"
        return time

    def normalize_time(self, time: str) -> Dict[str, str]:
        """
        Преобразует время в корректный формат для API.
        """
        time = time.replace("[", "").replace("]", "").replace("<", "").replace(">", "")
        splited_time = time.split(" ")
        time = "T".join(splited_time[:2])
        normal_time = time.replace(" ", "").replace("TT", "T").replace(";", "").replace("X", "0")
        if self.check_date(normal_time):
            return {'date': normal_time[:-2]}
        else:
            return {'dateTime': self.makefull(normal_time)}

    def get_time_from(self, content: Query) -> Dict[str, str]:
        """
        Извлекает начальное время из сообщения.
        """
        self.check_token()

        message = f'''Приведи начальное время из сообщения "{content.content}" в формат '[<дата>; <время>]'.'''

        time = self.normalize_time(self.request(message, 25).json()['choices'][0]['message']['content'])
        return time

    def get_time_to(self, content: Query) -> Dict[str, str]:
        """
        Извлекает конечное время из сообщения.
        """
        self.check_token()

        message = f'''Приведи конечное время из сообщения "{content.content}" в формат '[<дата>; <время>]'.'''

        time = self.normalize_time(self.request(message, 25).json()['choices'][0]['message']['content'])
        return time

    def get_description(self, content: Query) -> str:
        """
        Извлекает описание события из сообщения.
        """
        self.check_token()

        message = f'''Определи описание события из сообщения "{content.content}".'''

        return self.request(message, 10).json()['choices'][0]['message']['content']

    def parse_message(self, content: Query) -> Optional[Request]:
        """
        Основной метод парсинга сообщения пользователя.
        """
        try:
            parsed = Request(RequestType.ELSE, "", "", {}, None, None)
            parsed.type = self.get_type(content)

            if parsed.type == RequestType.EVENT:
                parsed.body = self.get_event_content(content)
                parsed.extra = self.get_description(content)
            elif parsed.type == RequestType.GOAL:
                parsed.body = self.get_task_content(content)

            parsed.timefrom = self.get_time_from(content)
            parsed.dateto = self.get_time_to(content)
            parsed.client_id = content.client_id

            if not parsed.body or not parsed.timefrom:
                return None

            return parsed
        except Exception as e:
            print(f"Ошибка парсинга сообщения: {e}")
            return None
