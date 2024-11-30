from dataclasses import dataclass
from datetime import datetime

@dataclass
class Query:
    """
        Client's query, forwarded from telebot to GPT_module
        
        Attributes
        __________
        client_id: str - telegram id in @<id> format
        
        current_time: datetime - current time and date
        
        content: str - query body
    """
    client_id: str
    current_time: datetime
    content: str

@dataclass
class RegistrationQuery:
    '''
        Client's query for registration
        
        Attributes
        __________
        client_id: str - telegram id in @<id> format
        
        Calendar_link: str
        
        Notion_link: str
    '''
    client_id: str
    Calendar_link: str
    Notion_link: str
