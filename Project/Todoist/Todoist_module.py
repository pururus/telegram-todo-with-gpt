import requests
from typing import Optional
from Project.Request import Request

class TodoistModule:
    """
    Класс для работы с API Todoist:
    - Проверка валидности токена (validate_token)
    - Создание задач (create_task)
    """

    def __init__(self, token: str):
        """
        Инициализирует TodoistModule с токеном API пользователя.

        Args:
            token (str): Токен доступа к Todoist API, полученный от пользователя.
        """
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def validate_token(self) -> bool:
        """
        Проверяет валидность Todoist API токена.

        Логика:
        1) Отправляем GET-запрос к /rest/v2/projects.
        2) Если статус 200, значит токен верный, возвращаем True.
        3) Иначе — False.

        Returns:
            bool: True, если токен валиден, False — если нет.
        """
        url = "https://api.todoist.com/rest/v2/projects"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return True
        return False

    def create_task(self, task_request: Request) -> Optional[str]:
        """
        Создаёт задачу в Todoist.

        Логика:
        1) Готовим запрос (POST) на /rest/v2/tasks.
        2) "content" = имя задачи (task_request.body).
        3) Если есть описание (extra), кладём в description.
        4) Если есть дата/время, передаём как due_string (только дату).
        5) При успехе возвращаем None, иначе строку с ошибкой.

        Args:
            task_request (Request): Объект Request с типом = GOAL, body = название задачи, extra = описание.

        Returns:
            Optional[str]: None, если всё ок. Иначе строка "Error code: ...".
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