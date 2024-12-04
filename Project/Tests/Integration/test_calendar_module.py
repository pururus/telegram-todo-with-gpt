# не работает

import pytest
from datetime import datetime
from Project.Calendar.Calendar_module import CalendarModule

@pytest.fixture
def MyCalendar():
    service_account_file = '/Users/liza/Documents/telegram-todo-with-gpt/Project/Calendar/to-do-443214-ed11f676b180.json'
    calendar = CalendarModule(service_account_file=service_account_file)
    return calendar

calendarId = '24399fbb12f20e1fdfaafd993ad4531dbe2675d11af0bd5dfa63a3292b503ef3@group.calendar.google.com'

def test_normal_event(MyCalendar):
    event = {
        'summary': 'test event',
        'description': 'normal one',
        'start': {
            'dateTime': '2024-11-30T13:00:00+03:00',
        },
        'end': {
            'dateTime': '2024-11-30T13:30:00+03:00',
        }
    }
    response = MyCalendar.create_event(event, calendarId)
    assert response is None

def test_event_with_date(MyCalendar):
    event = {
        'summary': 'test event',
        'description': 'only date',
        'start': {
            'date': '2023-11-30',
        },
        'end': {
            'date': '2023-12-01',
        },
    }
    response = MyCalendar.create_event(event, calendarId)
    assert response is None

def test_event_with_no_end(MyCalendar):
    event = {
        'summary': 'test event',
        'description': 'only date',
        'start': {
            'date': '2023-11-30',
        },
    }
    response = MyCalendar.create_event(event, calendarId)
    assert response is not None
    assert 'Missing end time.' in str(response)

def test_event_with_no_start(MyCalendar):
    event = {
        'summary': 'test event',
        'description': 'only date',
        'end': {
            'date': '2023-11-30',
        },
    }
    response = MyCalendar.create_event(event, calendarId)
    assert response is not None
    assert 'Start and end times must either both be date or both be dateTime.' in str(response)

def test_event_with_no_time(MyCalendar):
    event = {
        'summary': 'test event',
        'description': 'only date',
    }
    response = MyCalendar.create_event(event, calendarId)
    assert response is not None
    assert 'Missing end time.' in str(response)

def test_event_with_no_name(MyCalendar):
    event = {
        'description': 'normal one',
        'start': {
            'dateTime': '2024-11-30T13:00:00+03:00',
        },
        'end': {
            'dateTime': '2024-11-30T13:30:00+03:00',
        }
    }
    response = MyCalendar.create_event(event, calendarId)
    assert response is None

def test_event_with_no_name(MyCalendar):
    event = {
        'description': 'normal one',
        'start': {
            'dateTime': '2024-11-30T13:00:00+03:00',
        },
        'end': {
            'dateTime': '2024-11-30T13:30:00+03:00',
        }
    }
    response = MyCalendar.create_event(event, calendarId)
    assert response is None

def test_event_with_no_description(MyCalendar):
    event = {
        'summary': 'test event',
        'start': {
            'dateTime': '2024-11-30T13:00:00+03:00',
        },
        'end': {
            'dateTime': '2024-11-30T13:30:00+03:00',
        }
    }
    response = MyCalendar.create_event(event, calendarId)
    assert response is None

def test_big_event(MyCalendar):
    event = {
        'summary': 'test event',
        'description': 'big one',
        'location': 'NIUVSHE',
        'start': {
            'dateTime': '2024-11-30T13:00:00+03:00',
        },
        'end': {
            'dateTime': '2024-11-30T13:30:00+03:00',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }
    response = MyCalendar.create_event(event, calendarId)
    assert response is None
