import requests
import base64
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path

search_directory = Path('../')

for file_path in search_directory.rglob("Project"):
    project = file_path.resolve()

import sys

sys.path.append('project')

from Project.Query import Query
from Project.Request import Request, RequestType

from Project.GPT.credentials import cal_credentials

import logging

from typing import Dict, Optional

logging.captureWarnings(True)


class GPT:
    _token = None
    _url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    def get_token(self, auth_token, scope='GIGACHAT_API_PERS'):
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
            return response
        except requests.RequestException as e:
            print(f"Ошибка: {str(e)}")
            return -1

    def check_token(self):
        encoded_credentials = base64.b64encode(cal_credentials.encode('utf-8')).decode('utf-8')

        if self._token == None:
            self.token = self.get_token(encoded_credentials).json()['access_token']

    def request(self, message: str, max_tockens: int = 50, temp=1) -> str:
        payload = json.dumps({
            "model": "GigaChat",
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ],
            "stream": False,
            "max_tokens": max_tockens,
            "temerature": temp
        })

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        response = requests.request("POST", self._url, headers=headers, data=payload, verify=False)
        return response

    def get_type(self, content: Query) -> RequestType:
        self.check_token()

        message = f'''Вся информация, которую я упоминаю в этом чате, должна остаться строго в рамках этого чата. Не сохраняй её, не используй ни в каких других контекстах и не упоминай её нигде в будущем. Считай, что вся информация исчезает сразу после завершения беседы, и ты не знаешь, что она когда-либо существовала. Не сохраняй и не используй эти данные в других чатах или беседах.
                        Не используй какого-либо контекста кроме этого сообщения, считай его первым, которое ты видел.
                        Ты обрабатываешь сообщения от пользователя чат-бота с интеграцией календаря и todo-лист. У тебя лимит в 5 слов.
                        Пользователь отправил сообщение "{content.content}". Тебе нужно определить по сообщению, что хочет пользователь,
                        создать событие/мероприятие в календаре, создать задачу для выполнения в todo-лист, или же по сообщению это определить нельзя.
                        В случае мероприятия(например, контрольная, встреча или концерт) напиши 'event', если задача(например, купить продукты,
                        закрыть дедлайн) напиши 'task', инача непиши 'else' 
                        Напиши только тип!'''

        ans = (self.request(message, 100).json()['choices'][0]['message']['content']).lower()

        if "event" in ans or "событие" in ans or "мероприятие" in ans:
            return RequestType.EVENT
        elif "todo" in ans or "task" in ans:
            return RequestType.GOAL
        else:
            return RequestType.ELSE

    def get_event_content(self, content: Query) -> str:
        self.check_token()

        message = f'''Ты обрабатываешь сообщения от пользователя чат-бота с интеграцией календаря.
                        Пользователь отправил сообщение "{content.content}". Пользователь хочет поставить это
                        событие в календарь. Тебе нужно определить и выписать название этого события максимально полноценно.
                        Например сообщение "поставь на завтра встречу с олегом в 7" должно обрабатываться тобой
                        в "Встреча с Олегом". 
                        Напиши только название события!'''

        return self.request(message, 10).json()['choices'][0]['message']['content']

    def get_task_content(self, content: Query) -> str:
        self.check_token()

        message = f'''Ты обрабатываешь сообщения от пользователя чат-бота с интеграцией todo-листа.
                        Пользователь отправил сообщение "{content.content}". Пользователь хочет поставить эту
                        таску в todolist. Тебе нужно определить и выписать формулировку этой задачи максимально полноценно.
                        Например сообщение "мне нужно купить продукты завтра" должно обрабатываться тобой
                        в "Купить продукты". 
                        Напиши только формулировку задачи!
                        Не упоминай время и день!'''

        return self.request(message, 15).json()['choices'][0]['message']['content']

    def check_date(self, date: str) -> bool:
        return date[-1] == "T" or date.count("T") == 0

    def makefull(self, time: str) -> str:
        time = time.replace(";", '')
        if time.count(":") == 0:
            time += ":00:00"
        elif time.count(":") == 1:
            time += ":00"
        time += "+03:00"
        return time

    def normalize_time(self, time: str) -> Dict[str, str]:
        time = time.replace("[", "")
        time = time.replace("]", "")
        time = time.replace("<", "")
        time = time.replace(">", "")

        splited_time = time.split(" ")
        time = "T".join(splited_time[0:2])
        splited_time = time.split(";")
        normal_time = "T".join(splited_time[0:2])
        splited_time = time.split("-")
        normal_time = "-".join(splited_time[0:3])
        normal_time = normal_time.replace(" ", "")
        normal_time = normal_time.replace("TT", "T")
        normal_time = normal_time.replace(";", "")
        normal_time = normal_time.replace("X", "0")
        if self.check_date(normal_time):
            return {'date': normal_time[:-2]}
        else:
            return {'dateTime': self.makefull(normal_time)}

    def get_time_from(self, content: Query) -> Dict[str, str]:
        self.check_token()

        message = f'''f"У теья лимит в 5 слов
                        Ты умеешь писать только даты и часы
                        Не используй словва!
                        Преобразуй запрос '{content.content}' в формат '[<дата>; <время>]'. Учитывай, что текущее время - это {content.current_time.strftime("%Y-%m-%d %H:%M:%S")}.
                        Примеры:
                        "Поставь на сегодня встречу в 19:00, текущее время 2024-12-2 12:00:00" 
                        ответ: [2024-12-02; 19:00:00]
                        Поставь на завтра встречу в 16:00, текущее время 2024-12-02 12:00:00" 
                        ответ: [2024-12-03; 16:00:00]'''

        time = self.normalize_time(self.request(message, 25).json()['choices'][0]['message']['content'])
        if "date" in time and "завтра" in time["date"].lower():
            time["date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "date" in time and "послезавтра" in time["date"].lower():
            time["date"] = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        elif "dateTime" in time and "завтра" in time["dateTime"].lower():
            time["date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            time.pop("dateTime")
        elif "dateTime" in time and "послезавтра" in time["dateTime"].lower():
            time["date"] = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            time.pop("dateTime")
        return time

    def get_time_to(self, content: Query) -> Dict[str, str]:
        self.check_token()

        message = f'''f"У теья лимит в 5 слов!
                        Ты умеешь писать только даты и часы
                        Не используй словва!
                        Преобразуй запрос '{content.content}' в формат '[<дата конца события>; <время конца события>]'. Учитывай, что текущее время - это {content.current_time.strftime("%Y-%m-%d %H:%M:%S")}.
                        Примеры:
                        "Поставь на сегодня встречу в 19:00, текущее время 2024-12-2 12:00:00" 
                        ответ: [2024-12-02; 20:00:00]
                        Поставь на завтра встречу в 16:00, текущее время 2024-12-02 12:00:00" 
                        ответ: [2024-12-03; 17:00:00]
                        Поставь на сегодня встречу в 19:00 на 15 минут, текущее время 2024-12-2 12:00:00" 
                        ответ: [2024-12-02; 19:15:00]
                        Поставь на завтра встречу в 16:00 на полчаса, текущее время 2024-12-02 12:00:00" 
                        ответ: [2024-12-03; 16:30:00]'''

        time = self.normalize_time(self.request(message, 25).json()['choices'][0]['message']['content'])
        if "date" in time and "завтра" in time["date"].lower():
            time["date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if "date" in time and "послезавтра" in time["date"].lower():
            time["date"] = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        elif "dateTime" in time and "завтра" in time["dateTime"].lower():
            time["date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            time.pop("dateTime")
        elif "dateTime" in time and "послезавтра" in time["dateTime"].lower():
            time["date"] = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            time.pop("dateTime")
        return time

    def get_description(self, content: Query) -> str:
        self.check_token()

        message = f'''Ты обрабатываешь сообщения от пользователя чат-бота с интеграцией календаря.
                        Пользователь отправил сообщение "{content.content}". Пользователь хочет поставить это
                        событие в календарь. Тебе нужно определить и выписать описание этого события максимально полноценно.
                        Напиши только описание события!'''

        return self.request(message, 10).json()['choices'][0]['message']['content']

    def parse_message(self, content: Query) -> Optional[Request]:
        try:
            parsed = Request(RequestType.ELSE, "", "", {}, None, None)
            parsed.type = self.get_type(content)

            if parsed.type == RequestType.ELSE:
                parsed.type = self.get_type(content, temp=10)
                if parsed.type == RequestType.ELSE:
                    parsed.type = self.get_type(content, temp=100)
                    if parsed.type == RequestType.ELSE:
                        return None
            elif parsed.type == RequestType.EVENT:
                parsed.body = self.get_event_content(content)
                parsed.extra = self.get_description(content)
            else:
                parsed.body = self.get_task_content(content)

            parsed.timefrom = self.get_time_from(content)
            parsed.dateto = self.get_time_to(content)
            parsed.client_id = content.client_id

            return parsed
        except:
            return None
