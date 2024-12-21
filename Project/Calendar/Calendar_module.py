from __future__ import print_function
import googleapiclient
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pathlib import Path
from typing import Dict, Union

search_directory = Path('../')

for file_path in search_directory.rglob("to-do-443214-ed11f676b180.json"):
    p = file_path.resolve()

for file_path in search_directory.rglob("Project"):
    project = file_path.resolve()

import sys
sys.path.append('project')

from Request import Request

class CalendarModule:
    """
    Класс для взаимодействия с Google Calendar:
    - Создание событий
    - Проверка валидности calendar_id
    """

    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = p

    def __init__(self):
        """
        Инициализация:
        1) Загружаем учётные данные из сервисного аккаунта JSON (SERVICE_ACCOUNT_FILE).
        2) Создаём объект self.service для доступа к методам Google Calendar API.
        """
        credentials = service_account.Credentials.from_service_account_file(self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES)
        self.service = build('calendar', 'v3', credentials=credentials)

    def validate_calendar_id(self, calendar_id: str) -> bool:
        """
        Проверяет валидность переданного Google Calendar ID:
        1) Вызывает метод self.service.calendars().get(...) и ловит исключения.
        2) Если всё ок, возвращает True. Иначе — False.

        Args:
            calendar_id (str): Предполагаемый ID календаря Google.

        Returns:
            bool: True, если календарь найден и доступен; False, если нет.
        """
        try:
            result = self.service.calendars().get(calendarId=calendar_id).execute()
            if result:
                return True
        except googleapiclient.errors.HttpError:
            return False
        except Exception:
            return False
        return False

    def create_event(self, event: Union[Dict[str, str], Request], calendarId: str):
        """
        Создаёт событие в Google Calendar.

        Если event — это объект класса Request, мы преобразуем его
        в словарь, пригодный для передачи в API.

        Args:
            event (Union[Dict[str, str], Request]): Данные о событии или Request.
            calendarId (str): ID календаря, куда вставляем событие.

        Returns:
            None при успешном создании события, иначе строка с описанием ошибки.
        """
        if type(event) == Request:
            new_dict = {}
            new_dict['summary'] = event.body
            if event.extra:
                new_dict["description"] = event.extra
            # Приведение start и end к одинаковому формату
            if 'dateTime' in event.timefrom:
                new_dict["start"] = {"dateTime": event.timefrom['dateTime']}
                new_dict["end"] = {"dateTime": event.dateto.get('dateTime', event.timefrom['dateTime'])}
            else:
                new_dict["start"] = {"date": event.timefrom['date']}
                new_dict["end"] = {"date": event.dateto.get('date', event.timefrom['date'])}

            event = new_dict

        try:
            event_result = self.service.events().insert(calendarId=calendarId, body=event).execute()
            print('Event created: %s' % (event_result.get('id')))
        except googleapiclient.errors.HttpError as e:
            return e.reason
        except Exception as e:
            return e