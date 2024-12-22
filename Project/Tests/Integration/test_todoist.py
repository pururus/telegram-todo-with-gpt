import pytest
from datetime import datetime
from pathlib import Path

search_directory = Path('../')

for file_path in search_directory.rglob("Project"):
    project = file_path.resolve()
    
import sys
sys.path.append('project')

from Request import Request, RequestType
from Todoist.Todoist_module import TodoistModule
from Request import Request, RequestType

@pytest.fixture
def MyTodoist():
    todoist = TodoistModule(todoist_token)
    return todoist

todoist_token = "5c411c04352f2f5f61a144f475b39e09b592e85f"

pytest_plugins = ('pytest_asyncio',)

@pytest.mark.asyncio
async def test_normal_event(MyTodoist):
    event = Request(RequestType.EVENT, "client", "Test request", {"dateTime": "2024-12-12T12:12:12+03:00"}, {"dateTime": "2024-12-13T12:12:12+03:00"}, "optional")

    response = await (MyTodoist.create_task(event))
    assert response is None

@pytest.mark.asyncio
async def test_request_with_no_dateto(MyTodoist):
    event = Request(RequestType.EVENT, "client", "Test request", {"dateTime": "2024-12-12T12:12:12+03:00"}, None, "optional")

    response = await MyTodoist.create_task(event)
    assert response is None

@pytest.mark.asyncio
async def test_request_with_bad_timefrom(MyTodoist):
    event = Request(RequestType.EVENT, "client", "Test request", {"bad": "efkvhweljf"}, None, "optional")

    response = await MyTodoist.create_task(event)
    assert response is None

@pytest.mark.asyncio
async def test_validate_token(MyTodoist):
    res = await MyTodoist.validate_token()
    assert res

@pytest.mark.asyncio
async def test_validate_invalid_token():
    MyTodoist = TodoistModule("123")
    res = await MyTodoist.validate_token()
    assert not res