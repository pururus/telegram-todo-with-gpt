import pytest

from pathlib import Path

search_directory = Path('../')

for file_path in search_directory.rglob("Project"):
    project = file_path.resolve()
    
import sys
sys.path.append('project')

from Database.Database import ClientsDB, Errors

@pytest.fixture
def db():
    db = ClientsDB(":test_db:")
    return db

def test_add_client(db):
    assert db.add_client("@client_id", "calendar_id", "notion_id") > 0

def test_existing_client(db):
    assert db.add_client("@new_client_id", "new_calendar_id", "new_notion_id") > 0
    assert db.add_client("@new_client_id", "new_calendar_id", "new_notion_id") == Errors.INTEGRITY_ERROR
    
def test_get_info(db):
    assert db.add_client("@client_check_info_id", "new_calendar_id", "new_notion_id") > 0
    assert db.get_calendar_id("@client_check_info_id") == "new_calendar_id"
    assert db.get_todoist_token("@client_check_info_id") == "new_notion_id"

def test_get_info_no_client(db):
    assert db.get_calendar_id("@stranger") == None
    assert db.get_todoist_token("@stranger") == None