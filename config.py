import os
from dotenv import load_dotenv

load_dotenv()

# Телеграм бот настройки
BOT_TOKEN = os.getenv('BOT_TOKEN')

# База данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///musicbot.db')

# Папка для загрузки файлов
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/audio')

# Flask настройки
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

# Создаем папку для загрузок если её нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)