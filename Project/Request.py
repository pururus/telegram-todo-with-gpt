from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime
from typing import Dict

class RequestType(Enum):
    EVENT = "event"
    GOAL = "goal"
    ELSE = "else"

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
    timefrom: Dict[str, str]
    dateto: Optional[Dict[str, str]]
    extra: Optional[str]