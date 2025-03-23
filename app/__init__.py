from flask import Flask
from flasgger import Swagger
import secrets
from .config import Config
from .extensions import db
from .models import *  # подтягивает все модели
from .routes import main_blueprint
from .routes.uploader import uploader

def create_app():
    app = Flask(__name__)
    # 🧬 Безопасный ключ для сессии и flash-сообщений
    app.config["SECRET_KEY"] = secrets.token_hex(32)

    # Загружаем конфиг
    app.config.from_object(Config)

    # Инициализация экстеншенов
    db.init_app(app)

    # Регистрация маршрутов
    app.register_blueprint(main_blueprint)
    app.register_blueprint(uploader)

    # Создание БД
    with app.app_context():
        db.create_all()

    # Swagger UI
    Swagger(app)

    return app
