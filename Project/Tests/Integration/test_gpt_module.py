# не работает

import unittest
import asyncio
from Project.GPT.GPT_module import GPT
pytest_plugins = ('pytest_asyncio',)

class TestGPTIntegration(unittest.TestCase):
    def setUp(self):
        self.gpt = GPT()
        self.gpt.check_token()
        
    async def test_request_status_code(self):
        message = 'Тестовое сообщение для GPT'
        try:
            response = await self.gpt.request(message)
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            self.fail(f"GPT request failed with exception: {e}")

if __name__ == '__main__':
    unittest.main()
