from __future__ import print_function
import googleapiclient
from google.oauth2 import service_account
from googleapiclient.discovery import build
from Project.Request import Request

from pathlib import Path
from typing import Dict, Union

search_directory = Path('../')

for file_path in search_directory.rglob("to-do-443214-ed11f676b180.json"):
    p = file_path.resolve()

class CalendarModule:
    '''
    Module for inserting events in Google Calendar
    '''
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = p

    def __init__(self):
        '''
        Connecting to API
        
        No attributes
        '''
        credentials = service_account.Credentials.from_service_account_file(self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES)
        self.service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)

    def create_event(self, event: Union[Dict[str, str], Request], calendarId: str):
        '''
        Creates event in calendar
        
        Atributes
        ______________
        event: Dict[str, str]
        
        calendarId: str - the Id of calendar where inserting
        '''
        if type(event) == Request:
            new_dict = {}
            new_dict['summary'] = event.body
            if event.extra:
                new_dict["description"] = event.extra
            new_dict["start"] = event.timefrom
            if event.dateto:
                new_dict["end"] = event.dateto
            else:
                new_dict["end"] = event.timefrom
            
            event = new_dict
            
        try:
            event = self.service.events().insert(calendarId=calendarId, body=event).execute()
            print('Event created: %s' % (event.get('id')))
        except googleapiclient.errors.HttpError as e:
            return e.reason
        except Exception as e:
            return e
