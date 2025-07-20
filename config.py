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

# Режим работы (development/production)
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# URL для веб-приложения
if ENVIRONMENT == 'production':
    # В продакшене используйте HTTPS домен
    WEB_BASE_URL = os.getenv('WEB_BASE_URL', 'https://yourdomain.com')
    USE_WEBAPP_BUTTON = True
else:
    # В разработке используем HTTP localhost
    WEB_BASE_URL = f"http://{FLASK_HOST}:{FLASK_PORT}"
    USE_WEBAPP_BUTTON = False  # WebApp кнопки работают только с HTTPS

# Создаем папку для загрузок если её нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)