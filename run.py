#!/usr/bin/env python3
"""
Главный файл для запуска телеграм бота-песенника
Запускает и телеграм бота и веб-приложение одновременно
"""

import asyncio
import threading
import signal
import sys
import logging
from telegram_bot import main as run_bot
from web_app import app
import config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MusicBotService:
    def __init__(self):
        self.bot_thread = None
        self.web_thread = None
        self.running = False
    
    def start_web_app(self):
        """Запуск Flask веб-приложения"""
        logger.info(f"🌐 Запуск веб-приложения на http://{config.FLASK_HOST}:{config.FLASK_PORT}")
        app.run(
            host=config.FLASK_HOST,
            port=config.FLASK_PORT,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    
    def start_telegram_bot(self):
        """Запуск телеграм бота"""
        logger.info("🤖 Запуск Telegram бота...")
        run_bot()
    
    def start(self):
        """Запуск всех сервисов"""
        if not config.BOT_TOKEN:
            logger.error("❌ BOT_TOKEN не найден! Создайте файл .env и добавьте токен бота.")
            logger.error("Пример содержимого .env файла:")
            logger.error("BOT_TOKEN=your_telegram_bot_token_here")
            return
        
        self.running = True
        
        logger.info("🎵 Запуск музыкального бота-песенника...")
        logger.info("=" * 50)
        
        # Запускаем веб-приложение в отдельном потоке
        self.web_thread = threading.Thread(target=self.start_web_app, daemon=True)
        self.web_thread.start()
        
        # Даем время веб-серверу запуститься
        import time
        time.sleep(2)
        
        logger.info("✅ Сервисы запущены!")
        logger.info("=" * 50)
        logger.info(f"📱 Telegram бот: готов к работе")
        logger.info(f"🌐 Веб-интерфейс: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
        logger.info(f"📁 Папка загрузок: {config.UPLOAD_FOLDER}")
        logger.info("=" * 50)
        logger.info("💡 Инструкции:")
        logger.info("1. Откройте бота в Telegram и отправьте /start")
        logger.info("2. Отправьте аудио файл для добавления в библиотеку")
        logger.info("3. Используйте веб-интерфейс для прослушивания музыки")
        logger.info("4. Нажмите Ctrl+C для остановки")
        logger.info("=" * 50)
        
        # Запускаем телеграм бота в основном потоке
        try:
            self.start_telegram_bot()
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Остановка всех сервисов"""
        logger.info("\n🛑 Остановка сервисов...")
        self.running = False
        
        logger.info("✅ Все сервисы остановлены")
        sys.exit(0)

def signal_handler(signum, frame):
    """Обработчик сигнала для корректной остановки"""
    logger.info("\n🛑 Получен сигнал остановки...")
    service.stop()

if __name__ == "__main__":
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Создаем и запускаем сервис
    service = MusicBotService()
    
    try:
        service.start()
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
        sys.exit(1)