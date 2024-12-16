
import requests
from typing import Optional
from Project.Request import Request

class TodoistModule:
    def __init__(self, token: str):
        """
        Инициализирует TodoistModule с токеном API пользователя.

        :param token: Токен API пользователя Todoist.
        """
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def create_task(self, task_request: Request) -> Optional[str]:
        """
        Создаёт задачу в Todoist.

        :param task_request: Объект Request с информацией о задаче.
        :return: None при успешном создании или строка ошибки при неудаче.
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
                due_string = task_request.timefrom['dateTime'].split("T")[0]
            elif 'date' in task_request.timefrom:
                due_string = task_request.timefrom['date']
            if due_string:
                data["due_string"] = due_string  # Передаём в корректном формате

        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 200 or response.status_code == 204:
            return None  # Успех
        else:
            return f"Error {response.status_code}: {response.text}"