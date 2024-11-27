# Message broker

## Оглавление
1. [Описание](#описание)
2. [Стек технологий](#стек-технологий)
3. [Запуск проекта](#запуск-проекта)
4. [Maintainers](#maintainers)

## Описание

Проект использует **RabbitMQ** для обмена сообщениями. Он состоит из двух частей: **Producer** и **Consumer**. Producer публикует URL в очередь RabbitMQ, извлекая все внутренние ссылки с веб-страницы, а Consumer забирает сообщения из очереди извлекает внутренние ссылки и отправляет их обратно в очередь, образуя 'бесконеную обработку'

**Особенности проекта**:
- **Producer** извлекает все внутренние ссылки с веб-страницы и отправляет их в очередь RabbitMQ.
- **Consumer** извлекает сообщения из очереди RabbitMQ, извлекает ссылки и отправляет их обратно в очередь для дальнейшей обработки.
- Проект использует асинхронное программирование с помощью библиотеки `aiohttp` для HTTP-запросов, а также RabbitMQ для обмена сообщениями.

## Стек технологий
- Python
- RabbitMQ
- pika
- aiohttp


## Запуск проекта
1. Клонирование репозитория
`git clone 

2. Переход в папку с репозиторием
`cd <название папки в которую клонировали репозиторий>`

3. Запуск RabbitMQ

`docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management`

4. Создание виртуального окружения
Windows
`python -m venv venv`
Linux 
`python3 -m venv venv`

5. Активация виртуального окружения
Windows
`.\venv\Scripts\activate`
Linux
`source venv/bin/activate`

6. Установка зависимостей.
`pip install -r requirements.txt`

7. Установка переменных окружения. Файл .env
    **Подключение к RabbitMQ:**
    - `RABBITMQ_HOST` — хост RabbitMQ сервера. По умолчанию: `localhost`.
    - `RABBITMQ_QUEUE` — имя очереди RabbitMQ, с которой будет работать приложение. По умолчанию: `urls`.
    - `RABBITMQ_USER` — имя пользователя для подключения к RabbitMQ. По умолчанию: `guest`.
    - `RABBITMQ_PASS` — пароль для подключения к RabbitMQ. По умолчанию: `guest`.
    - `TIMEOUT` — таймаут в секундах для выполнения запросов. По умолчанию: `10`.

    #### Пример:
        `
        RABBITMQ_HOST=localhost
        RABBITMQ_QUEUE=urls
        RABBITMQ_USER=guest
        RABBITMQ_PASS=guest
        TIMEOUT=10
        `
    
8. Запуск Producer
    ```
    python producer.py <URL>
    ```
    Замените `<URL>` на нужный вам адрес страницы, с которой нужно извлечь ссылки.

9. Запуск Consumer
    ```
    python consumer.py
    ```
    Consumer будет извлекать ссылки из очереди и обрабатывать их по мере поступления.

## Полезные ссылки

- [RabbitMQ](https://www.rabbitmq.com)

## Maintainers

- Developed by [Pavel Demukhametov](https://github.com/Pavel-Demukhametov)

