import requests
from typing import Optional
from Request import Request
import aiohttp

class TodoistModule:
    """
    Класс для работы с API Todoist:
    1) Проверка валидности токена (validate_token).
    2) Создание задач (create_task).
    """

    def __init__(self, token: str):
        """
        Инициализирует TodoistModule с токеном API пользователя.

        Args:
            token (str): Токен API пользователя Todoist.
        """
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    async def validate_token(self) -> bool:
        """
        Проверяет валидность Todoist API токена.

        Логика:
        1) Отправляем GET-запрос к /rest/v2/projects.
        2) Если статус 200, значит токен верный, возвращаем True.
        3) Иначе — False.

        Returns:
            bool: True, если токен валиден, False — если нет.
        """
        url = "https://api.todoist.com/rest/v2/tasks"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, ssl=False) as response:
                if response.status == 200 or response.status == 204:
                    return True
                return False

    async def create_task(self, task_request: Request) -> Optional[str]:
        """
        Создаёт задачу в Todoist.

        Логика:
        1) Делаем POST-запрос на /rest/v2/tasks.
        2) 'content' = название задачи (task_request.body).
        3) Если есть описание (extra) — кладём в 'description'.
        4) Если есть дата/время — извлекаем дату (без времени) и передаём как 'due_string'.
        5) При успехе возвращаем None, иначе строку с ошибкой.

        Args:
            task_request (Request): Request с типом GOAL, body = имя задачи, extra = описание задачи.

        Returns:
            Optional[str]: None при успехе, иначе строка вида "Error <код>: <текст>".
        """
        url = "https://api.todoist.com/rest/v2/tasks"
        data = {
            "content": task_request.body
        }
        if task_request.extra:
            data["description"] = task_request.extra
        if task_request.timefrom:
            due_string = None
            if 'dateTime' in task_request.timefrom:
                # Извлекаем только дату из dateTime
                due_string = " at ".join(task_request.timefrom['dateTime'].split("+")[0].split("T"))
                print(due_string)
            elif 'date' in task_request.timefrom:
                due_string = task_request.timefrom['date']
            if due_string:
                data["due_string"] = due_string  # Передаём в корректном формате

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data, ssl=False) as response:
                if response.status == 200 or response.status == 204:
                    return None  # Успех
                else:
                    return f"Error {response.status_code}: {response.text}"

