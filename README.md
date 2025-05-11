# Foodgram - Продуктовый Помощник

Foodgram это RESTful API сервис для публикации рецептов, создания списков покупок и подписок на авторов.

## Технологии

*   Python 3.11
*   Django 4.2+ (или актуальная версия из requirements.txt)
*   Django REST framework
*   Djoser (для управления пользователями)
*   PostgreSQL (в качестве базы данных)
*   Nginx (в качестве веб-сервера и обратного прокси)
*   Docker / Docker Compose (для контейнеризации)
*   Gunicorn (WSGI HTTP сервер)


## Установка и запуск

1.  **Клонируйте репозиторий:**

    ```bash
    git clone <URL_вашего_репозитория>
    cd <имя_папки_проекта>
    ```

2.  **Настройка переменных окружения:**

    В корневой директории проекта создайте файл `.env` (на один уровень выше директории `backend`). Скопируйте содержимое из `.env.example` (если он есть) или создайте его со следующими переменными:

    ```env
    # Ключ Django (обязательно смените на свой в продакшене)
    DJANGO_SECRET_KEY='your_very_secret_django_key_here'

    # Режим отладки (True для разработки, False для продакшена)
    DEBUG=True

    # Параметры базы данных PostgreSQL
    POSTGRES_DB=foodgram_db
    POSTGRES_USER=foodgram_user
    POSTGRES_PASSWORD=foodgram_password
    DB_HOST=db # Имя сервиса базы данных в docker-compose.yml
    DB_PORT=5432

    # Разрешенные хосты (для продакшена укажите ваш домен)
    # ALLOWED_HOSTS=your_domain.com,www.your_domain.com,localhost,127.0.0.1
    ```
    **Важно:** Для продакшена установите `DEBUG=False` и заполните `ALLOWED_HOSTS`.

3.  **Сборка и запуск Docker контейнеров:**

    Перейдите в директорию, где находится ваш `docker-compose.yml` (обычно это корень проекта или директория `infra`).
    Если `docker-compose.yml` находится в корне проекта:
    ```bash
    docker-compose up --build
    ```
    Если `docker-compose.yml` находится в `infra/`:
    ```bash
    cd infra
    docker-compose up --build
    ```
    Эта команда соберет образы (если они еще не собраны) и запустит все сервисы, определенные в `docker-compose.yml`.

4.  **Применение миграций (после первого запуска контейнеров):**

    Откройте новый терминал и выполните команду, чтобы войти в контейнер `backend` и применить миграции:

    ```bash
    # Найти ID или имя контейнера backend (обычно что-то вроде project_backend_1)
    docker ps

    # Зайти в контейнер backend (замените <container_id_or_name> на актуальное значение)
    docker exec -it <container_id_or_name> bash

    # Внутри контейнера выполнить:
    python manage.py migrate
    python manage.py collectstatic --noinput
    # При необходимости, создайте суперпользователя:
    # python manage.py createsuperuser
    exit
    ```

5.  **Проект должен быть доступен:**
    *   API: `http://localhost/api/` (или порт, настроенный в `nginx.conf` и `docker-compose.yml`)
    *   Админ-панель Django: `http://localhost/admin/`

## API Документация

Спецификация API доступна в файле `openapi-schema.yml` в директории `docs/`.
Вы можете использовать Swagger Editor или другие инструменты для ее просмотра.
После запуска проекта документация также может быть доступна по адресу `http://localhost/api/docs/` (если настроено).

## Линтинг

Проект использует `flake8` для проверки стиля кода.

1.  **Установка `flake8` (если еще не установлен глобально или в виртуальном окружении):**
    ```bash
    pip install flake8
    ```
2.  **Запуск `flake8`:**
    Из корневой директории проекта (где находится директория `backend`):
    ```bash
    flake8 backend/
    ```
    Конфигурация `flake8` может находиться в файле `.flake8` или `setup.cfg`.

## Остановка проекта

Чтобы остановить все запущенные контейнеры:
```bash
# Если вы в директории с docker-compose.yml
docker-compose down


```

## Автор

*   [AleksandrKutarin]
