from __future__ import print_function
import googleapiclient
from google.oauth2 import service_account
from googleapiclient.discovery import build

class CalendarModule:
    '''
    Module for inserting events in Google Calendar
    '''
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = "../telegram-todo-with-gpt/Project/Calendar/to-do-443214-fbe8ee8bb440.json"

    def __init__(self):
        '''
        Connecting to API
        
        No attributes
        '''
        credentials = service_account.Credentials.from_service_account_file(self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES)
        self.service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)

    def create_event(self, event, calendarId):
        '''
        Creates event in calendar
        
        Atributes
        ______________
        event: Dict[str, str]
        
        calendarId: str - the Id of calendar where inserting
        '''
        try:
            event = self.service.events().insert(calendarId=calendarId, body=event).execute()
            print('Event created: %s' % (event.get('id')))
        except googleapiclient.errors.HttpError as e:
            return e.reason
        except Exception as e:
            return e

