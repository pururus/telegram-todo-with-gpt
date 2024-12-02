import requests

class NotionModule:
    """
    Класс для работы с API Notion.
    """
    BASE_URL = "https://api.notion.com/v1"
    HEADERS = {
        "Authorization": "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",  
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    def __init__(self, database_id: str):
        """
        Инициализация класса.
        :param database_id: Идентификатор базы данных Notion.
        """
        self.database_id = database_id

    def add_task(self, title: str, date: str, status: str = "Не выполнено"):
        """
        Добавляет новую задачу в базу данных Notion.
        :param title: Название задачи.
        :param date: Дата выполнения задачи (ISO 8601 формат: "YYYY-MM-DDTHH:MM:SS").
        :param status: Статус задачи ("Не выполнено", "Выполняется", "Выполнено").
        :return: Ответ от API.
        """
        url = f"{self.BASE_URL}/pages"
        data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Название": {
                    "title": [
                        {
                            "text": {"content": title}
                        }
                    ]
                },
                "Дата": {
                    "date": {"start": date}
                },
                "Статус": {
                    "select": {"name": status}
                }
            }
        }

        response = requests.post(url, headers=self.HEADERS, json=data)
        if response.status_code == 200:
            print("Задача успешно добавлена в Notion.")
        else:
            print(f"Ошибка добавления задачи: {response.text}")
        return response.json()

    def get_tasks(self):
        """
        Получает список задач из базы данных.
        :return: Список задач.
        """
        url = f"{self.BASE_URL}/databases/{self.database_id}/query"
        response = requests.post(url, headers=self.HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка получения задач: {response.text}")
            return None
