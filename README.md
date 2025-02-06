# **Foodgram — Продуктовый помощник**

**Foodgram** — это веб-приложение для обмена рецептами, подписки на любимых авторов и формирования списка покупок.
Зарегистрированные пользователи могут публиковать рецепты, добавлять их в избранное и получать автоматически сформированный список продуктов для покупки.

---

##  **Как запустить проект**

### ** Клонируйте репозиторий**
```sh
git clone https://github.com/your-username/foodgram.git
cd foodgram-st/infra
```

### ** Создайте файл `.env`**
В корне директории `infra/` создайте файл `.env` по примеру `.env.example`

### ** Запустите Docker**
```sh
docker-compose up -d --build
```

### ** Выполните миграции**
```sh
docker-compose exec backend python manage.py migrate
```

### ** Заполните базу ингредиентами**
```sh
docker-compose exec backend python manage.py load_data
```

### ** Создайте суперпользователя (админ)**
```sh
docker-compose exec backend python manage.py createsuperuser
```

После выполнения этих шагов приложение будет доступно по адресу **[http://localhost/](http://localhost/)**.

---

## **Полезные ссылки**

- **Интерфейс веб-приложения** → [http://localhost/](http://localhost/)
- **Спецификация API (Swagger)** → [http://localhost/api/docs/](http://localhost/api/docs/)
- **Панель администратора** → [http://localhost/admin/](http://localhost/admin/)

---

## **Технологии**
- **Backend:** Django, Django REST Framework, PostgreSQL
- **Frontend:** React
- **Развертывание:** Docker, Gunicorn, Nginx
