import os
from dotenv import load_dotenv

load_dotenv()  # 🧠 загружает переменные из .env

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///advisor.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
