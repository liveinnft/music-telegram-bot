import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Audio
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode
from mutagen import File as MutagenFile
from database import DatabaseManager
from models import create_tables
import config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для разговора
WAITING_FOR_TRACK_NAME = "waiting_for_track_name"
WAITING_FOR_ARTIST_NAME = "waiting_for_artist_name"
WAITING_FOR_ALBUM_NAME = "waiting_for_album_name"
WAITING_FOR_PLAYLIST_NAME = "waiting_for_playlist_name"
CHOOSING_DESTINATION = "choosing_destination"

class MusicBot:
    def __init__(self):
        self.user_states = {}
        self.temp_audio_data = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        db = DatabaseManager()
        try:
            user = db.get_or_create_user(
                telegram_id=update.effective_user.id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name,
                last_name=update.effective_user.last_name
            )
            
            keyboard = [
                [InlineKeyboardButton("🎵 Мои альбомы", callback_data="view_albums")],
                [InlineKeyboardButton("📝 Мои плейлисты", callback_data="view_playlists")],
            ]
            
            web_url = f"{config.WEB_BASE_URL}/web/{user.telegram_id}"
            
            # Добавляем WebApp кнопку только если поддерживается HTTPS
            if config.USE_WEBAPP_BUTTON:
                keyboard.append([InlineKeyboardButton("🌐 Веб-приложение", web_app={"url": web_url})])
                web_message = ""
            else:
                web_message = f"\n\n🌐 Веб-интерфейс: {web_url}"
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"Привет, {update.effective_user.first_name}! 👋\n\n"
                "Добро пожаловать в бота-песенника! 🎵\n\n"
                "Что умеет этот бот:\n"
                "• Добавлять аудио файлы в твою библиотеку\n"
                "• Создавать альбомы и плейлисты\n"
                "• Прослушивать добавленную музыку\n"
                "• Веб-интерфейс для удобного управления\n\n"
                f"Просто отправь мне аудио файл, чтобы начать! 🎧{web_message}",
                reply_markup=reply_markup
            )
        finally:
            db.close()
    
    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик аудио файлов"""
        audio: Audio = update.message.audio
        user_id = update.effective_user.id
        
        # Получаем информацию о файле
        file = await context.bot.get_file(audio.file_id)
        
        # Создаем безопасное имя файла
        file_extension = os.path.splitext(audio.file_name or "audio.mp3")[1] or ".mp3"
        safe_filename = f"{audio.file_id}{file_extension}"
        file_path = os.path.join(config.UPLOAD_FOLDER, safe_filename)
        
        # Скачиваем файл
        await file.download_to_drive(file_path)
        
        # Получаем метаданные
        try:
            audio_file = MutagenFile(file_path)
            title = audio.title or (audio_file.get('TIT2', [None])[0] if audio_file else None) or "Неизвестный трек"
            artist = audio.performer or (audio_file.get('TPE1', [None])[0] if audio_file else None) or "Неизвестный исполнитель"
            duration = audio.duration or (audio_file.info.length if audio_file else None)
        except:
            title = audio.title or "Неизвестный трек"
            artist = audio.performer or "Неизвестный исполнитель"
            duration = audio.duration
        
        # Сохраняем временные данные
        self.temp_audio_data[user_id] = {
            'title': title,
            'artist': artist,
            'file_path': file_path,
            'file_id': audio.file_id,
            'duration': int(duration) if duration else None
        }
        
        # Получаем альбомы и плейлисты пользователя
        db = DatabaseManager()
        try:
            user = db.get_or_create_user(telegram_id=user_id)
            albums = db.get_user_albums(user.id)
            playlists = db.get_user_playlists(user.id)
            
            keyboard = []
            
            if albums:
                keyboard.append([InlineKeyboardButton("📀 Выбрать альбом", callback_data="choose_album")])
            
            if playlists:
                keyboard.append([InlineKeyboardButton("📝 Выбрать плейлист", callback_data="choose_playlist")])
            
            keyboard.extend([
                [InlineKeyboardButton("➕ Создать новый альбом", callback_data="create_album")],
                [InlineKeyboardButton("➕ Создать новый плейлист", callback_data="create_playlist")]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"🎵 Получен трек:\n"
                f"🎤 <b>{artist}</b>\n"
                f"📄 <b>{title}</b>\n\n"
                f"Куда добавить этот трек?",
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        finally:
            db.close()
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        db = DatabaseManager()
        try:
            user = db.get_or_create_user(telegram_id=user_id)
            
            if data == "view_albums":
                await self.show_albums(query, db, user.id)
            elif data == "view_playlists":
                await self.show_playlists(query, db, user.id)
            elif data == "choose_album":
                await self.show_albums_for_selection(query, db, user.id)
            elif data == "choose_playlist":
                await self.show_playlists_for_selection(query, db, user.id)
            elif data == "create_album":
                await self.start_album_creation(query, user_id)
            elif data == "create_playlist":
                await self.start_playlist_creation(query, user_id)
            elif data.startswith("album_"):
                await self.handle_album_action(query, db, data)
            elif data.startswith("playlist_"):
                await self.handle_playlist_action(query, db, data)
            elif data.startswith("track_"):
                await self.send_track(query, db, data)
            elif data.startswith("add_to_album_"):
                await self.add_track_to_album(query, db, user.id, data)
            elif data.startswith("add_to_playlist_"):
                await self.add_track_to_playlist(query, db, user.id, data)
        finally:
            db.close()
    
    async def show_albums(self, query, db: DatabaseManager, user_id: int):
        """Показать список альбомов"""
        albums = db.get_user_albums(user_id)
        
        if not albums:
            keyboard = [[InlineKeyboardButton("➕ Создать альбом", callback_data="create_album")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📀 У вас пока нет альбомов.\nСоздайте первый альбом!",
                reply_markup=reply_markup
            )
            return
        
        keyboard = []
        for album in albums:
            track_count = len(db.get_album_tracks(album.id))
            keyboard.append([InlineKeyboardButton(
                f"📀 {album.name} ({track_count} треков)", 
                callback_data=f"album_{album.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("➕ Создать альбом", callback_data="create_album")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text("📀 Ваши альбомы:", reply_markup=reply_markup)
    
    async def show_playlists(self, query, db: DatabaseManager, user_id: int):
        """Показать список плейлистов"""
        playlists = db.get_user_playlists(user_id)
        
        if not playlists:
            keyboard = [[InlineKeyboardButton("➕ Создать плейлист", callback_data="create_playlist")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📝 У вас пока нет плейлистов.\nСоздайте первый плейлист!",
                reply_markup=reply_markup
            )
            return
        
        keyboard = []
        for playlist in playlists:
            track_count = len(db.get_playlist_tracks(playlist.id))
            keyboard.append([InlineKeyboardButton(
                f"📝 {playlist.name} ({track_count} треков)", 
                callback_data=f"playlist_{playlist.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("➕ Создать плейлист", callback_data="create_playlist")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text("📝 Ваши плейлисты:", reply_markup=reply_markup)
    
    async def show_albums_for_selection(self, query, db: DatabaseManager, user_id: int):
        """Показать альбомы для выбора при добавлении трека"""
        albums = db.get_user_albums(user_id)
        
        keyboard = []
        for album in albums:
            keyboard.append([InlineKeyboardButton(
                f"📀 {album.name}", 
                callback_data=f"add_to_album_{album.id}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📀 Выберите альбом:", reply_markup=reply_markup)
    
    async def show_playlists_for_selection(self, query, db: DatabaseManager, user_id: int):
        """Показать плейлисты для выбора при добавлении трека"""
        playlists = db.get_user_playlists(user_id)
        
        keyboard = []
        for playlist in playlists:
            keyboard.append([InlineKeyboardButton(
                f"📝 {playlist.name}", 
                callback_data=f"add_to_playlist_{playlist.id}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📝 Выберите плейлист:", reply_markup=reply_markup)
    
    async def handle_album_action(self, query, db: DatabaseManager, data: str):
        """Обработка действий с альбомом"""
        album_id = int(data.split("_")[1])
        album = db.get_album_by_id(album_id)
        tracks = db.get_album_tracks(album_id)
        
        if not tracks:
            await query.edit_message_text(f"📀 Альбом '{album.name}' пуст.")
            return
        
        keyboard = []
        for track in tracks:
            keyboard.append([InlineKeyboardButton(
                f"🎵 {track.artist} - {track.title}",
                callback_data=f"track_{track.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("« Назад", callback_data="view_albums")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📀 <b>{album.name}</b>\n\nТреки:",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def handle_playlist_action(self, query, db: DatabaseManager, data: str):
        """Обработка действий с плейлистом"""
        playlist_id = int(data.split("_")[1])
        playlist = db.get_playlist_by_id(playlist_id)
        tracks = db.get_playlist_tracks(playlist_id)
        
        if not tracks:
            await query.edit_message_text(f"📝 Плейлист '{playlist.name}' пуст.")
            return
        
        keyboard = []
        for track in tracks:
            keyboard.append([InlineKeyboardButton(
                f"🎵 {track.artist} - {track.title}",
                callback_data=f"track_{track.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("« Назад", callback_data="view_playlists")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📝 <b>{playlist.name}</b>\n\nТреки:",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def send_track(self, query, db: DatabaseManager, data: str):
        """Отправка трека пользователю"""
        track_id = int(data.split("_")[1])
        track = db.get_track_by_id(track_id)
        
        if not track:
            await query.answer("Трек не найден", show_alert=True)
            return
        
        try:
            if track.file_id:
                # Используем сохраненный file_id для быстрой отправки
                await query.message.reply_audio(
                    audio=track.file_id,
                    caption=f"🎵 {track.artist} - {track.title}"
                )
            else:
                # Отправляем файл по пути
                with open(track.file_path, 'rb') as audio_file:
                    await query.message.reply_audio(
                        audio=audio_file,
                        title=track.title,
                        performer=track.artist,
                        caption=f"🎵 {track.artist} - {track.title}"
                    )
        except Exception as e:
            logger.error(f"Ошибка при отправке трека: {e}")
            await query.answer("Ошибка при отправке трека", show_alert=True)
    
    async def add_track_to_album(self, query, db: DatabaseManager, user_id: int, data: str):
        """Добавление трека в альбом"""
        album_id = int(data.split("_")[-1])
        
        if user_id not in self.temp_audio_data:
            await query.answer("Данные о треке утеряны", show_alert=True)
            return
        
        audio_data = self.temp_audio_data[user_id]
        user = db.get_or_create_user(telegram_id=user_id)
        
        track = db.add_track(
            user_id=user.id,
            title=audio_data['title'],
            artist=audio_data['artist'],
            file_path=audio_data['file_path'],
            file_id=audio_data['file_id'],
            duration=audio_data['duration'],
            album_id=album_id
        )
        
        album = db.get_album_by_id(album_id)
        
        # Очищаем временные данные
        del self.temp_audio_data[user_id]
        
        await query.edit_message_text(
            f"✅ Трек добавлен в альбом '{album.name}'!\n\n"
            f"🎵 {audio_data['artist']} - {audio_data['title']}"
        )
    
    async def add_track_to_playlist(self, query, db: DatabaseManager, user_id: int, data: str):
        """Добавление трека в плейлист"""
        playlist_id = int(data.split("_")[-1])
        
        if user_id not in self.temp_audio_data:
            await query.answer("Данные о треке утеряны", show_alert=True)
            return
        
        audio_data = self.temp_audio_data[user_id]
        user = db.get_or_create_user(telegram_id=user_id)
        
        track = db.add_track(
            user_id=user.id,
            title=audio_data['title'],
            artist=audio_data['artist'],
            file_path=audio_data['file_path'],
            file_id=audio_data['file_id'],
            duration=audio_data['duration'],
            playlist_id=playlist_id
        )
        
        playlist = db.get_playlist_by_id(playlist_id)
        
        # Очищаем временные данные
        del self.temp_audio_data[user_id]
        
        await query.edit_message_text(
            f"✅ Трек добавлен в плейлист '{playlist.name}'!\n\n"
            f"🎵 {audio_data['artist']} - {audio_data['title']}"
        )
    
    async def start_album_creation(self, query, user_id: int):
        """Начать создание альбома"""
        self.user_states[user_id] = WAITING_FOR_ALBUM_NAME
        await query.edit_message_text("📀 Введите название для нового альбома:")
    
    async def start_playlist_creation(self, query, user_id: int):
        """Начать создание плейлиста"""
        self.user_states[user_id] = WAITING_FOR_PLAYLIST_NAME
        await query.edit_message_text("📝 Введите название для нового плейлиста:")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text
        
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]
        db = DatabaseManager()
        
        try:
            user = db.get_or_create_user(telegram_id=user_id)
            
            if state == WAITING_FOR_ALBUM_NAME:
                album = db.create_album(user.id, text)
                del self.user_states[user_id]
                
                # Если есть временный трек, предлагаем добавить в новый альбом
                if user_id in self.temp_audio_data:
                    keyboard = [[InlineKeyboardButton(
                        f"➕ Добавить в '{album.name}'", 
                        callback_data=f"add_to_album_{album.id}"
                    )]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"✅ Альбом '{album.name}' создан!\n\nДобавить текущий трек в этот альбом?",
                        reply_markup=reply_markup
                    )
                else:
                    await update.message.reply_text(f"✅ Альбом '{album.name}' создан!")
            
            elif state == WAITING_FOR_PLAYLIST_NAME:
                playlist = db.create_playlist(user.id, text)
                del self.user_states[user_id]
                
                # Если есть временный трек, предлагаем добавить в новый плейлист
                if user_id in self.temp_audio_data:
                    keyboard = [[InlineKeyboardButton(
                        f"➕ Добавить в '{playlist.name}'", 
                        callback_data=f"add_to_playlist_{playlist.id}"
                    )]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"✅ Плейлист '{playlist.name}' создан!\n\nДобавить текущий трек в этот плейлист?",
                        reply_markup=reply_markup
                    )
                else:
                    await update.message.reply_text(f"✅ Плейлист '{playlist.name}' создан!")
        
        finally:
            db.close()

def main():
    """Запуск бота"""
    # Создаем таблицы БД
    create_tables()
    
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN не найден в переменных окружения!")
        return
    
    # Создаем бота
    bot = MusicBot()
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.AUDIO, bot.handle_audio))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text_message))
    application.add_handler(CallbackQueryHandler(bot.button_handler))
    
    # Запускаем бота
    logger.info("Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()