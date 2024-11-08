# Telegram Todo with GPT

## Описание проекта

Телеграм бот, который по сообщению в свободном формате формирует событие и отмечает его в Google Calendar или добавляет задачу в Notion. Бот помогает сэкономить время, обрабатывая неструктурированные текстовые запросы и создавая удобные напоминания и задачи.

---

## Примерный сценарий взаимодействия

1. **Первоначальная настройка**:
   - Пользователь отправляет `/start`, и бот предлагает ввести ссылки на календарь и Notion.
   - После подтверждения настроек бот приветствует пользователя и предлагает помощь.

2. **Добавление события**:
   - Пользователь отправляет сообщение вроде “Запланируй встречу с Олегом завтра в 15:20”.
   - Бот парсит сообщение, распознавая ключевые элементы (время, название, место) и предлагает пользователю уточнить или подтвердить.
   - После подтверждения бот создает событие в Google Calendar и отправляет подтверждение с деталями.

3. **Добавление задачи**:
   - Пользователь пишет “Напомни сходить за продуктами в воскресенье”.
   - Бот парсит по ключевым словам и создает задачу в Notion. Пользователю приходит сообщение с подтверждением.

---

## Структура проекта

![image](https://github.com/pururus/telegram-todo-with-gpt/blob/main/Todo-with-gpt_structure.jpg)

**Telegram Bot**: 
   - Пользовательский интерфейс. При первом использовании запрашивает у пользователя ссылки на его календарь и todo-list. Полученную информацию регистрирует в базе данных
   - Принимает сообщения от пользователя и формирует из них запрос, содержащий текст сообщения, id пользователя, время и дату сообщения, после чего отправляет запрос процессору.
   - После выполнения запроса возвращает пользователю ответ.

**Registration module**:
   - Принимает данные регистрации от пользователя, проверяет их на корректность и, при корректрости, отправляет их в БД, иначе возвращает сообщение об ошибке

**База данных**:
   - Содержит информацию о пользователях: id в telegram, ссылки на Notion и Google Calendar, статус регистрации

**GPT parser**
   - Обрабатывает сообщение от пользователя, вместе с датой и временем сообщения
   - Формирует форматированный запрос
   - Отправляет запрос в Processor

**Processor**:
   - Обрабатывает запрос
   - Получает данные из БД
   - Отправляет данные в нужный модуль
   - Возвразает в Telegram module возможные сообщения об ошибке

**Notion module и Google Calendar module**:
   - Формирует событие или задачу

---

## Распределение по ролям

- **Святослав Полонский** (tg: [@pururus](https://t.me/pururus))
  - Работа с запросами через API GPT
  - Работа с Google Calendar
  - Работа с базой данных пользователей

- **Лиза Зорькина** (tg: [@lizyn](https://t.me/lizyn))
  - Frontend (сам бот)
  - API Notion
