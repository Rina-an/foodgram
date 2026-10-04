# Foodgram

[![Foodgram workflow](https://github.com/Rina-an/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/Rina-an/foodgram/actions/workflows/main.yml)

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



## Как запустить проект
1. `git clone https://github.com/Rina-an/foodgram.git`
2. Перейти в папку проекта `cd <pwd>/foodgram`
3. Создать виртуальное окружение `python3 -m venv venv`
4. Активировать его `source venv/bin/activate`
5. Установить зависимости `pip install -r requirements.txt`
7. Создать в корне проекта файл `.env` по образцу `.env.example`.
7. Перейти в папку `infra` и выполнить `docker compose up --build`.
9. В соседнем терминале выполнить:

```
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
docker compose exec backend python manage.py load_ingredients
docker compose exec backend python manage.py load_test_data
```

Сайт будет доступен по адресу `https://ktq.servemp3.com/`.

## Переменные окружения

| Переменная          | Назначение                     |
| ------------------- | ------------------------------ |
| `POSTGRES_USER`     | Имя пользователя PostgreSQL    |
| `POSTGRES_PASSWORD` | Пароль пользователя PostgreSQL |
| `POSTGRES_DB`       | Название базы данных           |
| `DB_HOST`           | Хост базы данных               |
| `DB_PORT`           | Порт базы данных               |
| `SECRET_KEY`        | Секретный ключ Django          |
| `DEBUG`             | Режим отладки Django           |
| `ALLOWED_HOSTS`     | Разрешённые домены и IP-адреса |

Файл `.env` не должен добавляться в репозиторий, так как он содержит конфиденциальные данные.


## CI/CD

В проекте настроен workflow GitHub Actions, который:

1. запускает backend-тесты и проверку Flake8;
2. собирает Docker-образы backend, frontend и gateway;
3. публикует образы в Docker Hub;
4. выполняет деплой на сервер;
5. отправляет уведомление об успешном деплое в Telegram.

Сборка и публикация Docker-образов выполняются при push в ветку `main`.

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
