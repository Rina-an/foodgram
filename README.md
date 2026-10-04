# Foodgram

«Фудграм» — сайт, на котором пользователи публикуют рецепты, добавляют чужие рецепты в избранное и подписываются на публикации других авторов. Зарегистрированным пользователям доступен сервис «Список покупок»: он позволяет собрать продукты для выбранных рецептов и скачать итоговый список одним файлом. У каждого рецепта есть короткая ссылка, которой удобно делиться.


## 🛠 Стек технологий

* **Backend:**
  * `Python 3.12`, `Django 5.2`, `Django REST Framework`, `Djoser`, `django-filter`
* **Frontend:**
  * `React` (SPA, собирается в контейнере `frontend`)
* **База данных:**
  * `PostgreSQL` — в продакшене, `SQLite` — для локальной разработки
* **Инфраструктура:**
  * `Docker`, `Docker Compose`, `Nginx`, `Gunicorn`, `GitHub Actions`


## Структура проекта

```
foodgram/
├── backend/                 Django-проект
│   ├── foodgram/            настройки проекта
│   ├── users/               пользователи и подписки
│   ├── recipes/             теги, ингредиенты, рецепты, избранное, список покупок,
│   │                        короткие ссылки и management-команды
│   └── api/                 REST API
│       ├── serializers.py   все сериализаторы API
│       ├── views.py         все вьюсеты API
│       ├── filters.py, pagination.py, permissions.py, fields.py
│       └── urls.py
├── data/                    ингредиенты (JSON и CSV)
├── docs/                    спецификация API (ReDoc)
├── frontend/                React-приложение
├── infra/                   nginx, Dockerfile шлюза, docker-compose для локального запуска
├── docker-compose.production.yml
└── .github/workflows/main.yml
```


## Как запустить локально (без Docker)

Для запуска необходимо в терминале перейти в папку с проектом и выполнить следующие команды:

1. `python3 -m venv venv` (Linux и macOS) или `python -m venv venv` (Windows)
2. `source venv/bin/activate` (Linux и macOS) или `source venv/Scripts/activate` (Windows)
3. `pip install -r backend/requirements.txt`
4. Перейти в папку `backend` и выполнить миграции: `python manage.py migrate`
5. Загрузить ингредиенты: `python manage.py load_ingredients`
6. Создать тестовые данные (теги, пользователи, рецепты): `python manage.py load_test_data`
7. `DEBUG=True python manage.py runserver`

Если переменная окружения `POSTGRES_DB` не задана, используется SQLite.
API будет доступен по адресу `http://127.0.0.1:8000/api/`.


## Как запустить в Docker локально

1. Создать в корне проекта файл `.env` по образцу `.env.example`.
2. Перейти в папку `infra` и выполнить `docker compose up --build`.
3. В соседнем терминале выполнить:

```
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
docker compose exec backend python manage.py load_ingredients
docker compose exec backend python manage.py load_test_data
```

Сайт будет доступен по адресу `http://localhost`, спецификация API — `http://localhost/api/docs/`, админка — `http://localhost/admin/`.


## Деплой на сервер (CI/CD)

При пуше в ветку `main` GitHub Actions:

1. проверяет код `flake8`, миграции и запуск проекта на PostgreSQL;
2. собирает образы `foodgram_backend`, `foodgram_frontend`, `foodgram_gateway` и пушит их в Docker Hub;
3. копирует `docker-compose.production.yml` на сервер, перезапускает контейнеры, применяет миграции, собирает статику и загружает ингредиенты.

### Подготовка сервера

1. Установить Docker и Docker Compose.
2. Создать папку `~/foodgram` и положить в неё файл `.env` (см. `.env.example`).
3. Контейнер `gateway` слушает порт `8000`. Во внешнем nginx сервера настроить проксирование:

```
location / {
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://127.0.0.1:8000;
}
```

### Секреты репозитория (Settings → Secrets and variables → Actions)

| Секрет | Значение |
|---|---|
| `DOCKER_USERNAME` | логин Docker Hub |
| `DOCKER_PASSWORD` | пароль или токен Docker Hub |
| `HOST` | IP-адрес сервера |
| `USER` | имя пользователя на сервере |
| `SSH_KEY` | закрытый SSH-ключ |
| `SSH_PASSPHRASE` | пароль от SSH-ключа |

### Тестовые данные на сервере

```
cd foodgram
sudo docker compose -f docker-compose.production.yml exec backend python manage.py load_test_data
```

Команда создаёт теги «Завтрак», «Обед», «Ужин», пользователей с разными уровнями доступа
(`admin@foodgram.ru` — суперпользователь, `moderator@foodgram.ru` — персонал,
`ivan@foodgram.ru` и `olga@foodgram.ru` — обычные пользователи) и по одному рецепту от каждого.
Пароль задаётся переменной окружения `TEST_USERS_PASSWORD` (по умолчанию `Foodgram2026!`).


## Примеры запросов и ответов API

Полная спецификация доступна по адресу `/api/docs/`.

- POST /api/auth/token/login/

Получение токена по email и паролю.

```
{
  "email": "vpupkin@yandex.ru",
  "password": "Qwerty123"
}
```

Ответ:

```
{
  "auth_token": "string"
}
```

- GET /api/recipes/?tags=breakfast&is_favorited=1&limit=6

Список рецептов с фильтрацией по тегам, автору, избранному и списку покупок.

```
{
  "count": 123,
  "next": "http://foodgram.example.org/api/recipes/?page=2",
  "previous": null,
  "results": [
    {
      "id": 0,
      "tags": [{"id": 0, "name": "Завтрак", "slug": "breakfast"}],
      "author": {
        "email": "user@example.com",
        "id": 0,
        "username": "string",
        "first_name": "Вася",
        "last_name": "Иванов",
        "is_subscribed": false,
        "avatar": "http://foodgram.example.org/media/users/image.png"
      },
      "ingredients": [
        {"id": 0, "name": "Картофель отварной", "measurement_unit": "г", "amount": 1}
      ],
      "is_favorited": true,
      "is_in_shopping_cart": false,
      "name": "string",
      "image": "http://foodgram.example.org/media/recipes/images/image.png",
      "text": "string",
      "cooking_time": 1
    }
  ]
}
```

- POST /api/recipes/

Создание рецепта. Картинка передаётся в Base64.

```
{
  "ingredients": [{"id": 1123, "amount": 10}],
  "tags": [1, 2],
  "image": "data:image/png;base64,iVBORw0KGgo...",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}
```

- GET /api/recipes/{id}/get-link/

```
{
  "short-link": "https://foodgram.example.org/s/3d0/"
}
```

- GET /api/recipes/download_shopping_cart/

Возвращает файл `shopping_list.txt`, в котором одинаковые ингредиенты из разных рецептов суммируются.


## Автор
* **Андреева Арина** — [GitHub](https://github.com/Rina-an)
