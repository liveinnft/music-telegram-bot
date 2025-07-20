from sqlalchemy.orm import Session
from models import User, Album, Playlist, Track, get_db
from typing import List, Optional

class DatabaseManager:
    def __init__(self):
        self.db = get_db()
    
    def close(self):
        self.db.close()
    
    # Методы для работы с пользователями
    def get_or_create_user(self, telegram_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None) -> User:
        user = self.db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return user
    
    # Методы для работы с альбомами
    def create_album(self, user_id: int, name: str, description: str = None) -> Album:
        album = Album(
            name=name,
            description=description,
            user_id=user_id
        )
        self.db.add(album)
        self.db.commit()
        self.db.refresh(album)
        return album
    
    def get_user_albums(self, user_id: int) -> List[Album]:
        return self.db.query(Album).filter(Album.user_id == user_id).all()
    
    def get_album_by_id(self, album_id: int) -> Optional[Album]:
        return self.db.query(Album).filter(Album.id == album_id).first()
    
    # Методы для работы с плейлистами
    def create_playlist(self, user_id: int, name: str, description: str = None) -> Playlist:
        playlist = Playlist(
            name=name,
            description=description,
            user_id=user_id
        )
        self.db.add(playlist)
        self.db.commit()
        self.db.refresh(playlist)
        return playlist
    
    def get_user_playlists(self, user_id: int) -> List[Playlist]:
        return self.db.query(Playlist).filter(Playlist.user_id == user_id).all()
    
    def get_playlist_by_id(self, playlist_id: int) -> Optional[Playlist]:
        return self.db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    # Методы для работы с треками
    def add_track(self, user_id: int, title: str, artist: str, file_path: str, 
                  file_id: str = None, duration: int = None, 
                  album_id: int = None, playlist_id: int = None) -> Track:
        track = Track(
            title=title,
            artist=artist,
            file_path=file_path,
            file_id=file_id,
            duration=duration,
            album_id=album_id,
            playlist_id=playlist_id,
            user_id=user_id
        )
        self.db.add(track)
        self.db.commit()
        self.db.refresh(track)
        return track
    
    def get_album_tracks(self, album_id: int) -> List[Track]:
        return self.db.query(Track).filter(Track.album_id == album_id).all()
    
    def get_playlist_tracks(self, playlist_id: int) -> List[Track]:
        return self.db.query(Track).filter(Track.playlist_id == playlist_id).all()
    
    def get_all_user_tracks(self, user_id: int) -> List[Track]:
        return self.db.query(Track).filter(Track.user_id == user_id).all()
    
    def get_track_by_id(self, track_id: int) -> Optional[Track]:
        return self.db.query(Track).filter(Track.id == track_id).first()
    
    def delete_track(self, track_id: int) -> bool:
        track = self.get_track_by_id(track_id)
        if track:
            self.db.delete(track)
            self.db.commit()
            return True
        return False
    
    def delete_album(self, album_id: int) -> bool:
        album = self.get_album_by_id(album_id)
        if album:
            self.db.delete(album)
            self.db.commit()
            return True
        return False
    
    def delete_playlist(self, playlist_id: int) -> bool:
        playlist = self.get_playlist_by_id(playlist_id)
        if playlist:
            self.db.delete(playlist)
            self.db.commit()
            return True
        return False