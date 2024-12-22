# работает
import unittest

from pathlib import Path

search_directory = Path('../')
for file_path in search_directory.rglob("Project"):
    project = file_path.resolve()

import sys
sys.path.append('project')

from unittest.mock import patch
from datetime import datetime
from GPT.GPT_module import GPT
from Query import Query
from Request import RequestType
import asyncio

class TestGPTModule(unittest.TestCase):
    def setUp(self):
        self.gpt = GPT()

    @patch('GPT.GPT_module.GPT.request')
    async def test_get_type_event(self, mock_request):
        # Замокаем ответ от GPT.request для типа 'event'
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'event'
                }
            }]
        }
        mock_request.return_value.json.return_value = mock_response

        content = Query(
            client_id='test_client',
            current_time=datetime.now(),
            content='Поставь встречу завтра в 15:00'
        )
        result = await self.gpt.get_type(content)
        self.assertEqual(result, RequestType.EVENT)

    @patch('GPT.GPT_module.GPT.request')
    async def test_get_type_task(self, mock_request):
        # Замокаем ответ от GPT.request для типа 'task'
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'task'
                }
            }]
        }
        mock_request.return_value.json.return_value = mock_response

        content = Query(
            client_id='test_client',
            current_time=datetime.now(),
            content='Нужно купить продукты'
        )
        result = await self.gpt.get_type(content)
        self.assertEqual(result, RequestType.GOAL)

    @patch('GPT.GPT_module.GPT.request')
    async def test_get_event_content(self, mock_request):
        # Замокаем ответ от GPT.request для названия события
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Встреча с командой'
                }
            }]
        }
        mock_request.return_value.json.return_value = mock_response

        content = Query(
            client_id='test_client',
            current_time=datetime.now(),
            content='Поставь встречу с командой завтра в 15:00'
        )
        result = await self.gpt.get_event_content(content)
        self.assertEqual(result, 'Встреча с командой')

    @patch('GPT.GPT_module.GPT.request')
    async def test_normalize_time(self, mock_request):
        # Мокаем ответ GPT.request для времени
        mock_response = {
            'choices': [{
                'message': {
                    'content': '[2024-12-03; 16:00:00]'
                }
            }]
        }
        mock_request.return_value.json.return_value = mock_response

        content = Query(
            client_id='test_client',
            current_time=datetime(2024, 12, 2, 12, 0, 0),
            content='Поставь встречу завтра в 16:00'
        )
        time = await self.gpt.get_time_from(content)
        expected_time = {'dateTime': '2024-12-03T16:00:00+03:00'}
        self.assertEqual(time, expected_time)

if __name__ == '__main__':
    unittest.main()
