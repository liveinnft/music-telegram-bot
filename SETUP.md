# 🎵 Инструкция по установке и запуску

## Быстрый старт

### 1. Установка зависимостей

```bash
# Создание виртуального окружения
python3 -m venv venv

# Активация виртуального окружения
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Создание Telegram бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Введите имя вашего бота (например: "Мой Музыкальный Бот")
   - Введите username бота (должен заканчиваться на `bot`, например: `my_music_bot`)
4. Сохраните полученный токен

### 3. Настройка конфигурации

```bash
# Скопируйте файл конфигурации
cp .env.example .env

# Отредактируйте .env файл
nano .env  # или любой другой редактор
```

Заполните `.env` файл:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
DATABASE_URL=sqlite:///musicbot.db
UPLOAD_FOLDER=uploads/audio
FLASK_SECRET_KEY=your-super-secret-key-here
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
```

### 4. Запуск

```bash
# Запуск всех сервисов
python run.py
```

После запуска будут доступны:
- 🤖 **Telegram бот**: готов принимать сообщения
- 🌐 **Веб-интерфейс**: http://127.0.0.1:5000

### 5. Первое использование

1. **В Telegram:**
   - Найдите вашего бота по username
   - Отправьте `/start`
   - Отправьте аудио файл боту

2. **В веб-интерфейсе:**
   - Откройте ссылку из сообщения бота
   - Или перейдите по адресу: `http://127.0.0.1:5000/web/YOUR_TELEGRAM_ID`

## Возможные проблемы и решения

### Ошибка: "BOT_TOKEN не найден"
- Убедитесь, что файл `.env` создан и содержит корректный токен
- Проверьте, что токен скопирован полностью без лишних пробелов

### Ошибка: "Permission denied" при создании папки uploads
```bash
mkdir -p uploads/audio
chmod 755 uploads/audio
```

### Порт 5000 уже занят
Измените порт в `.env` файле:
```env
FLASK_PORT=5001
```

### Проблемы с зависимостями
```bash
# Переустановка зависимостей
pip install --upgrade -r requirements.txt

# Для старых версий Python
pip install --upgrade pip setuptools wheel
```

## Развертывание в продакшене

### PythonAnywhere

1. Загрузите файлы проекта
2. Создайте виртуальное окружение:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.8 musicbot
   pip install -r requirements.txt
   ```

3. Настройте веб-приложение:
   - Создайте новое веб-приложение
   - Укажите путь к `web_app.py`
   - Настройте WSGI файл

4. Запустите бота:
   - Создайте Always-On Task с командой: `python telegram_bot.py`

### Heroku

1. Создайте `Procfile`:
   ```
   web: python web_app.py
   worker: python telegram_bot.py
   ```

2. Добавьте переменные окружения в Heroku Dashboard

3. Деплой:
   ```bash
   git add .
   git commit -m "Initial commit"
   heroku create your-app-name
   git push heroku main
   ```

### GitHub Pages (только веб-часть)

Для размещения статической версии веб-интерфейса на GitHub Pages потребуется:

1. Создать статические HTML файлы
2. Настроить API для работы с внешним сервером
3. Адаптировать JavaScript для работы без Flask

## Структура проекта

```
telegram-music-bot/
├── 📄 run.py              # Главный файл запуска
├── 📄 telegram_bot.py     # Логика Telegram бота
├── 📄 web_app.py          # Flask веб-приложение
├── 📄 database.py         # Работа с базой данных
├── 📄 models.py           # Модели SQLAlchemy
├── 📄 config.py           # Конфигурация
├── 📁 templates/          # HTML шаблоны
├── 📁 static/             # CSS, JS, изображения
├── 📁 uploads/            # Загруженные аудио файлы
└── 📄 requirements.txt    # Python зависимости
```

## Полезные команды

```bash
# Просмотр логов
tail -f logs/bot.log

# Остановка всех процессов
pkill -f "python run.py"

# Очистка базы данных
rm musicbot.db

# Резервное копирование
tar -czf backup.tar.gz uploads/ musicbot.db .env

# Восстановление
tar -xzf backup.tar.gz
```

## Контакты и поддержка

При возникновении проблем:
1. Проверьте логи
2. Убедитесь в корректности конфигурации
3. Создайте issue в репозитории

---

**Удачного использования! 🎵**