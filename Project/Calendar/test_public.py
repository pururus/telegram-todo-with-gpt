import pytest
from datetime import datetime
from Calendar_module import CalendarModule

@pytest.fixture
def MyCalendar():
    calendar = CalendarModule()
    return calendar

calendarId = '24399fbb12f20e1fdfaafd993ad4531dbe2675d11af0bd5dfa63a3292b503ef3@group.calendar.google.com'

def test_normal_event(MyCalendar):
    event = {'summary': 'test event',
            'description': 'normal one',
            'start': {
                'dateTime': '2024-11-30T13:00:00+03:00',
            },
            'end': {
                'dateTime': '2024-11-30T13:30:00+03:00',
            }
            }
    
    assert MyCalendar.create_event(event, calendarId) == None
    
def test_event_with_date(MyCalendar):
    event = {'summary': 'test event',
    'description': 'only date',
    'start': {
        'date': '2023-11-30',
    },
    'end': {
        'date': '2023-12-1',
    },
}
    
    assert MyCalendar.create_event(event, calendarId) == None

def test_event_with_no_end(MyCalendar):
    event = {'summary': 'test event',
    'description': 'only date',
    'start': {
        'date': '2023-11-30',
    },
}
    
    assert MyCalendar.create_event(event, calendarId) == "Missing end time."

def test_event_with_no_start(MyCalendar):
    event = {'summary': 'test event',
    'description': 'only date',
    'end': {
        'date': '2023-11-30',
    },
}
    
    assert MyCalendar.create_event(event, calendarId) == "Start and end times must either both be date or both be dateTime."

def test_event_with_no_time(MyCalendar):
    event = {'summary': 'test event',
    'description': 'only date',
}
    
    assert MyCalendar.create_event(event, calendarId) == "Missing end time."

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
    
    assert MyCalendar.create_event(event, calendarId) == None

def test_event_with_no_description(MyCalendar):
    event = {
            'start': {
                'dateTime': '2024-11-30T13:00:00+03:00',
            },
            'end': {
                'dateTime': '2024-11-30T13:30:00+03:00',
            }
            }
    
    assert MyCalendar.create_event(event, calendarId) == None

def test_big_event(MyCalendar):
    event = {'summary': 'test event',
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
    
    assert MyCalendar.create_event(event, calendarId) == None
    