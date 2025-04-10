import requests
import base64
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import aiohttp

search_directory = Path('../')

for file_path in search_directory.rglob("Project"):
    project = file_path.resolve()

import sys
sys.path.append('project')

from Query import Query
from Request import Request, RequestType

from GPT.credentials import cal_credentials

import logging
from typing import Dict, Optional

logging.captureWarnings(True)

class GPT:
    _token = None
    _model = "GigaChat-Max"
    _url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    async def get_token(self, auth_token, scope='GIGACHAT_API_PERS'):
        '''
        Функция возвращает API токен для gigachat
        
        :param auth_token: Закодированные client_id и секретный ключ
        '''
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
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=payload, ssl=False) as response:
                    return await response.json()
        except aiohttp.ClientError as e:
            print(f"Ошибка: {str(e)}")
            return -1

    async def check_token(self):
        '''
        Проверяет, получен ли API токен, и, если нет, устанавливает токен в соответствующее поле.
        '''
        if self._token is None:
            encoded_credentials = base64.b64encode(cal_credentials.encode('utf-8')).decode('utf-8')
            self._token = (await self.get_token(encoded_credentials))["access_token"]

    async def request(self, message: str, max_tockens: int = 50, temp=1):
        '''
        Функция для запросов к API
        
        :param message: Сообщение, отправляемое LLM
        :param max_tockens: Максимальное количество токенов в ответе
        :param temp: Температура. Влияет на ответ
        
        :return: словарь
        '''
        payload = json.dumps({
            "model": self._model,
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
            'Authorization': f'Bearer {self._token}'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self._url, headers=headers, data=payload, ssl=False) as response:
                return await response.json()

    async def get_type(self, content: Query, temp=1) -> RequestType:
        '''
        Получает тип запроса пользователя. 
        
        :param content: Запрос пользователя
        :param temp: Температура. Влияет на ответ
        
        :return: RequestType
        '''
        
        await self.check_token()

        message = f'''Вся информация, которую я упоминаю в этом чате, должна остаться строго в рамках этого чата. Не сохраняй её, не используй ни в каких других контекстах и не упоминай её нигде в будущем. Считай, что вся информация исчезает сразу после завершения беседы, и ты не знаешь, что она когда-либо существовала. Не сохраняй и не используй эти данные в других чатах или беседях.
                        Не используй какого-либо контекста кроме этого сообщения, считай его первым, которое ты видел.
                        Ты обрабатываешь сообщения от пользователя чат-бота с интеграцией календаря и todo-лист. У тебя лимит в 8 слов. 
        Пользователь отправил сообщение: "{content.content}". Твоя задача — определить, хочет ли пользователь:
        1. Создать событие в календаре (например, встреча, контрольная, концерт, какой-нибудь праздник, экзамен, поездка, и так далее).
        2. Создать задачу для выполнения в todo-листе (например, купить продукты, обнять друга, покормить котят, сделать дз, и так далее).
        Если пользователь хочет создать событие, напиши "event". Если это задача, напиши "task". Если невозможно определить, напиши "else".

        Примеры:
        1. "Сделать домашнее задание" -> task
        2. "Обнять Костю" -> task
        3. "Встреча с Олегом завтра в 19:00" -> event
        4. "Купить продукты" -> task
        5. "Посмотреть фильм с друзьями" -> task
        6. "Позвонить маме в воскресенье" -> task
        7. "Покормить бездомных собак" -> task
        8. "Репетиция хора в 18:00" -> event
        9. "Собрание в школе в пятницу" -> event
        10. "Приготовить ужин для семьи" -> task
        11. "Сходить на каток с друзьями" -> task
        12. "День рождения Анны завтра в 18:00" -> event
        13. "Подготовка к контрольной в среду" -> task
        14. "Встреча с заказчиком через неделю" -> event
        15. "Уборка квартиры" -> task

        Напиши только тип ("event", "task" или "else")!'''

        try:
            ans = ((await self.request(message, 100, temp))['choices'][0]['message']['content']).lower()
        except Exception as e:
            print(e)
            if "Max" in self._model:
                self._model = "GigaChat-Pro"
                return RequestType.ELSE
            else:
                self._model = "GigaChat"
                return RequestType.ELSE
        
        if "event" in ans or "событие" in ans or "мероприятие" in ans:
            return RequestType.EVENT
        elif "todo" in ans or "task" in ans:
            return RequestType.GOAL
        else:
            return RequestType.ELSE

    async def get_event_content(self, content: Query) -> str:
        '''
        Получает название события из сообщения пользователя. 
        
        :param content: Запрос пользователя
        
        :return: название события
        '''
        
        await self.check_token()

        message = f'''Ты обрабатываешь сообщения от пользователя чат-бота с интеграцией календаря. 
        Пользователь отправил сообщение "{content.content}". Пользователь хочет поставить это событие в календарь.Твоя задача — определить название события максимально понятно, сохранить важную информацию и эмоции.

        Примеры:
        1. "Встреча с Олегом завтра в 19:00" -> "Встреча с Олегом"
        2. "Праздник у бабушки в субботу" -> "Праздник у бабушки"
        3. "Репетиция рэпа" -> "Репетиция рэпа"
        4. "Контрольная по матанализу в пятницу" -> "Контрольная по матанализу"
        5. "День рождения Анечки завтра в 18:00" -> "День рождения Анечки"
        6. "Собрание в школе в пятницу" -> "Собрание в школе"
        7. "Свадьба у Лехи через неделю" -> "Свадьба у Лехи"
        8. "Поездка на природу с друзьями" -> "Поездка на природу"
        9. "Презентация проекта в на покре" -> "Презентация проекта"
        10. "Курсы по программированию" -> "Курсы по программированию"
        11. "Экзамен в университете" -> "Экзамен"
        12. "кошачья посиделка в ресторане" -> "Кошачья посиделка"
        13. "тренировка по алгоритмам" -> "Тренировка по алгоритмам"
        14. "Свидание с девушкой из тиндера в кафе" -> "Свидание с девушкой из тиндера"
        15. "тусовка на крыше" -> "Тусовка на крыше"

        Напиши только название события, без времени и других деталей!'''

        return (await self.request(message, 10))['choices'][0]['message']['content']

    async def get_task_content(self, content: Query) -> str:
        '''
        Получает название задачи из сообщения пользователя. 
        
        :param content: Запрос пользователя
        
        :return: название задачи
        '''
        
        self.check_token()

        message = f'''Ты обрабатываешь сообщения от пользователя чат-бота с интеграцией todo-листа. 
        Пользователь отправил сообщение "{content.content}". Пользователь хочет поставить эту таску в todolist. Твоя задача — определить и выписать формулировку задачи максимально просто и понятно, но сохранить эмоциональную окраску, если она есть.

        Примеры:
        1. "Нужно купить продукты" -> "Купить продукты"
        2. "Обнять Костю" -> "Обнять Костю"
        3. "Позвонить маме" -> "Позвонить маме"
        4. "Надо сделать домашнее задание" -> "Сделать домашнее задание"
        5. "Покормить котят" -> "Покормить котят"
        6. "Как-нибудь помочь бабушке по хозяйству" -> "Помочь бабушке по хозяйству"
        7. "Убраться где-то на кухне" -> "Убраться на кухне"
        8. "Погладить бельё" -> "Погладить бельё"
        9. "Пока есть время прочитать книгу" -> "Прочитать книгу"
        10. "Написать Насте про шляпу" -> "Написать Насте про шляпу"
        11. "Поцеловать парня" -> "Поцеловать парня"
        12. "Сходить в спортзал" -> "Сходить в спортзал"
        13. "Собрать чемодан для поездки" -> "Собрать чемодан"
        14. "Покормить бездомных собак" -> "Покормить бездомных собак"
        15. "побегать вокруг кровати" -> "побегать вокруг кровати"

        Напиши только текст задачи, без времени или других деталей!'''

        return (await self.request(message, 15))['choices'][0]['message']['content']

    async def check_date(self, date: str) -> bool:
        '''
        Проверяет что строка, полученная от normalize_time, является датой 
        
        :param date: Строка от normalize_time
        
        :return: bool
        '''
        
        return date[-1] == "T" or date.count("T") == 0

    async def makefull(self, time: str) -> str:
        '''
        Приводит строку dateTime в формат yyyy-mm-ddThh:mm:ss+03:00
        
        :param time: Строка от normalize_time
        
        :return: yyyy-mm-ddThh:mm:ss+03:00
        '''
        
        parts = time.split("T")
        if len(parts) == 1:
            time = f"{parts[0]}T00:00:00+03:00"  # Дата без времени
        elif len(parts) == 2:
            if ":" not in parts[1]:
                time = f"{parts[0]}T{parts[1]}:00:00+03:00"
            elif parts[1].count(":") == 1:
                time = f"{parts[0]}T{parts[1]}:00+03:00"
            else:
                time = f"{parts[0]}T{parts[1]}+03:00"
        return time

    async def normalize_time(self, time: str) -> Dict[str, str]:
        """
        НИЖЕ — ключевая правка, чтобы при отсутствии реальной даты
        возвращать пустой словарь {}, а не {'date': ''}.
        """
        time = time.replace("[", "").replace("]", "")
        time = time.replace("<", "").replace(">", "")

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

        # Если строка пустая/слишком короткая => нет даты => вернуть {}
        if not normal_time or len(normal_time) < 4:
            return {}

        if await self.check_date(normal_time):
            # Если заканчивается "T" или "-" => у нас обрезок => вернуть {}
            if normal_time.endswith("T") or normal_time.endswith("-"):
                return {}
            # Можно оставить как у вас: {'date': normal_time[:-2]}
            # Но если normal_time[:-2] короче 4 символов => пусто
            # => значит вернём {}
            if len(normal_time[:-2]) < 4:
                return {}
            return {'date': normal_time[:-2]}
        else:
            dt = await self.makefull(normal_time)
            if len(dt) < 10:
                return {}
            dt = dt.replace("T24", "T23")
            return {'dateTime': dt}

    async def get_time_from(self, content: Query) -> Dict[str, str]:
        '''
        Получает дату(и время) начала события из сообщения пользователя. 
        
        :param content: Запрос пользователя
        
        :return: дату(и время)
        '''
        
        await self.check_token()

        message = f'''Ты обрабатываешь сообщения от пользователя чат-бота с интеграцией календаря. Ты умеешь писать только даты и часы. Не используй слова!!!! У тебя лимит в 5-6 слов.
        Преобразуй запрос "{content.content}" в формат даты и времени начала события: "[<дата>; <время>]". Учитывай, что текущее время: {content.current_time.strftime("%Y-%m-%d %H:%M:%S")}.

        Примеры: (пример если сегодня 2024-12-21)
        1. "Поставь на сегодня встречу в 19:00" -> [2024-12-21; 19:00:00]
        2. "Встреча завтра в 16:00" -> [2024-12-22; 16:00:00]
        3. "На послезавтра тренировка в 10 утра" -> [2024-12-23; 10:00:00]
        4. "Митап в пятницу в 15:30" -> [2024-12-27; 15:30:00]
        5. "На следующей неделе собрание в 14:00" -> [2024-12-28; 14:00:00]
        6. "Покормить вечером бездомных собак в девять" -> [2024-12-21; 21:00:00]
        7. "Покормить котят в час дня" -> [2024-12-21; 13:00:00]
        8. "Экзамен по алгебре послезавтра в три часа дня" -> [2024-12-23; 15:00:00 ]'''

        raw = (await self.request(message, 25))['choices'][0]['message']['content']
        time = await self.normalize_time(raw)
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

    async def get_time_to(self, content: Query) -> Dict[str, str]:
        '''
        Получает дату(и время) конца события/дедлайн из сообщения пользователя. 
        
        :param content: Запрос пользователя
        
        :return: дату(и время)
        '''
        
        await self.check_token()

        message = f'''f"У тебя лимит в 5 слов!
                        Ты умеешь писать только даты и часы
                        Не используй слова!
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

        message = f'''Ты обрабатываешь сообщения от пользователя чат-бота с интеграцией календаря. У тебя лимит в 5 слов! Ты умеешь писать только даты и часы. Не используй слова!!!!
        Преобразуй запрос "{content.content}" в формат даты и времени окончания события: "[<дата конца события>; <время конца события>]". Учитывай, что текущее время: {content.current_time.strftime("%Y-%m-%d %H:%M:%S")}.

        Примеры: (пример если сегодня 2024-12-21)
        1. "Поставь на сегодня встречу в 19:00" -> [2024-12-21; 20:00:00]
        2. "Встреча завтра в 16:00 на час" -> [2024-12-22; 17:00:00]
        3. "На послезавтра тренировка в 10 утра, длится 2 часа" -> [2024-12-23; 12:00:00]
        4. "Митап в пятницу в 15:30 на полчаса" -> [2024-12-27; 16:00:00]
        5. "На следующей неделе собрание в 14:00 до 15:30" -> [2024-12-28; 15:30:00]
        6. "Покормить котят в час дня" -> [2024-12-21; 14:00:00]
        7. "Экзамен по алгебре послезавтра в три часа дня" -> [2024-12-21; 18:00:00]
'''

        raw = (await self.request(message, 25))['choices'][0]['message']['content']
        time = await self.normalize_time(raw)
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

    async def get_description(self, content: Query) -> str:
        '''
        Получает описание события из сообщения пользователя. 
        
        :param content: Запрос пользователя
        
        :return: описание
        '''
        
        await self.check_token()

        message = f'''Ты обрабатываешь сообщения от пользователя чат-бота с интеграцией календаря.
                        Пользователь отправил сообщение "{content.content}". Пользователь хочет поставить это
                        событие в календарь. Тебе нужно определить и выписать описание этого события максимально полноценно.
                        Напиши только описание события!'''

        return (await self.request(message, 10))['choices'][0]['message']['content']

    async def better_times(self, parsed: Request):
        '''
        Упорядочивает даты
        '''
        if "dateTime" in parsed.dateto and "dateTime" in parsed.timefrom:
            parsed.timefrom["dateTime"], parsed.dateto["dateTime"] = min(parsed.timefrom["dateTime"], parsed.dateto["dateTime"]), max(parsed.timefrom["dateTime"], parsed.dateto["dateTime"])
        else:
            parsed.dateto = parsed.timefrom
        return parsed
    
    async def parse_message(self, content: Query) -> Optional[Request]:
        '''
        Парсит сообщение пользователя
        '''
        try:
            parsed = Request(RequestType.ELSE, "", "", {}, None, None)
            parsed.type = await self.get_type(content)

            if parsed.type == RequestType.ELSE:
                parsed.type = await self.get_type(content, temp=10)
                if parsed.type == RequestType.ELSE:
                    parsed.type = await self.get_type(content, temp=100)
                    if parsed.type == RequestType.ELSE:
                        return None
            elif parsed.type == RequestType.EVENT:
                
                parsed.body, parsed.extra, parsed.timefrom, parsed.dateto = await asyncio.gather(
                                                                                self.get_event_content(content),
                                                                                self.get_description(content),
                                                                                self.get_time_from(content),
                                                                                self.get_time_to(content))
                # Для EVENT мы идём дальше, получаем timefrom/timeTo
                parsed = await self.better_times(parsed)
            else:
                # Если it's a task => body = get_task_content
                parsed.body, parsed.timefrom = await asyncio.gather(self.get_task_content(content), self.get_time_from(content))
                # КЛЮЧЕВОЕ: НЕ вызываем get_time_from / get_time_to => нет даты => FIX
                # parsed.timefrom = {}
                # parsed.dateto = {}
                # Если хотите всё же попытаться вынуть дату => можно оставить,
                # но тогда, если GPT всё же вернёт мусор => InvalidDate.
                # Так что лучше вообще не заполнять для задач.
                parsed.dateto = {}

            parsed.client_id = content.client_id

            return parsed
        except Exception as e:
            logging.exception("Ошибка в parse_message: %s", e)
            return None
