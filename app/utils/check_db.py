from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    print("🔌 Проверка подключения к PostgreSQL...")
    conn = db.engine.connect()
    print("✅ Успешно подключено к:", db.engine.url)
    print("📦 Таблицы:", db.engine.table_names())
