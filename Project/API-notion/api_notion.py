from notion_client import Client

# Создаём клиента для работы с Notion
notion = Client(auth="Ваш_секретный_ключ")  # Подставьте сюда ваш Integration Secret

# Функция для добавления задачи в базу данных Notion
def add_task_to_notion(database_id, task_name, task_due_date):
    """
    Добавляет задачу в базу данных Notion.

    :param database_id: Идентификатор базы данных (Database ID).
    :param task_name: Название задачи.
    :param task_due_date: Дата выполнения задачи в формате YYYY-MM-DD.
    :return: Статус выполнения (успех или ошибка).
    """
    try:
        notion.pages.create(
            parent={"database_id": database_id},  # ID базы данных Notion
            properties={
                "Name": {  # Название задачи
                    "title": [
                        {
                            "text": {
                                "content": task_name
                            }
                        }
                    ]
                },
                "Due Date": {  # Дата выполнения задачи
                    "date": {
                        "start": task_due_date
                    }
                }
            }
        )
        return "Задача успешно добавлена в Notion!"  # Успешный результат
    except Exception as e:
        return f"Ошибка: {e}"  # Возвращаем текст ошибки
