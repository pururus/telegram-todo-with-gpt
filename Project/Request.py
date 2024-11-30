from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime

class RequestType(Enum):
    EVENT = "event"
    GOAL = "goal"

@dataclass
class Request:
    """
        Processed request forwarded to processor
        
        Attributes
        __________
        type: RequestType - event or goal
        
        client_id: str - telegram id in @<id> format
        
        body: str - name of goal or event
        
        date: str - date in DD.MM.YYYY format
        
        time: str - time in HH:MM format
        
        extra: Optional[str] - some optional information
        
    """
    type: RequestType
    client_id: str
    body: str
    date: str
    time: str
    extra: Optional[str]