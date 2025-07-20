from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import config

# Создаем базовый класс для моделей
Base = declarative_base()

# Модель пользователя
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    albums = relationship("Album", back_populates="user", cascade="all, delete-orphan")
    playlists = relationship("Playlist", back_populates="user", cascade="all, delete-orphan")

# Модель альбома
class Album(Base):
    __tablename__ = 'albums'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="albums")
    tracks = relationship("Track", back_populates="album", cascade="all, delete-orphan")

# Модель плейлиста
class Playlist(Base):
    __tablename__ = 'playlists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="playlists")
    tracks = relationship("Track", back_populates="playlist", cascade="all, delete-orphan")

# Модель трека
class Track(Base):
    __tablename__ = 'tracks'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    artist = Column(String(200))
    file_path = Column(String(500), nullable=False)
    file_id = Column(String(200))  # Telegram file_id для быстрой отправки
    duration = Column(Integer)  # Длительность в секундах
    album_id = Column(Integer, ForeignKey('albums.id'))
    playlist_id = Column(Integer, ForeignKey('playlists.id'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    album = relationship("Album", back_populates="tracks")
    playlist = relationship("Playlist", back_populates="tracks")
    user = relationship("User")

# Создание движка и сессии базы данных
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создание таблиц
def create_tables():
    Base.metadata.create_all(bind=engine)

# Функция для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Сессия будет закрыта в коде использующем её