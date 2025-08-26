# BookShop

Интернет-магазин книг на Flask с регистрацией пользователей, корзиной и оформлением заказов.

---

## Требования

- Python 3.10+
- PostgreSQL (или SQLite для локальной разработки)
- Все зависимости указаны в `requirements.txt`

---

## Установка

1. Клонируем репозиторий:

```bash
git clone https://github.com/username/bookshop.git
cd bookshop
```

## Установка зависимостей

pip install -r requirements.txt

## Создаем файл .enc
В корне проекта и указываем переменные окружения:

DATABASE_URL =postgresql://user:password@localhost:5432/bookshop
SECRET_KEY = your_secret_key
APP_PORT = any_port
DEBUG = True|False

## Проект готов к запуску
