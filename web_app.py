from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
import os
import json
from database import DatabaseManager
from models import create_tables
import config

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY
CORS(app)

# Создаем таблицы при запуске
create_tables()

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/web/<int:telegram_id>')
def user_dashboard(telegram_id):
    """Личный кабинет пользователя"""
    db = DatabaseManager()
    try:
        user = db.get_or_create_user(telegram_id=telegram_id)
        albums = db.get_user_albums(user.id)
        playlists = db.get_user_playlists(user.id)
        all_tracks = db.get_all_user_tracks(user.id)
        
        return render_template('dashboard.html', 
                             user=user, 
                             albums=albums, 
                             playlists=playlists,
                             all_tracks=all_tracks,
                             telegram_id=telegram_id)
    finally:
        db.close()

@app.route('/api/user/<int:telegram_id>/tracks')
def get_user_tracks(telegram_id):
    """API для получения всех треков пользователя"""
    db = DatabaseManager()
    try:
        user = db.get_or_create_user(telegram_id=telegram_id)
        tracks = db.get_all_user_tracks(user.id)
        
        tracks_data = []
        for track in tracks:
            track_data = {
                'id': track.id,
                'title': track.title,
                'artist': track.artist,
                'duration': track.duration,
                'created_at': track.created_at.isoformat() if track.created_at else None,
                'album': track.album.name if track.album else None,
                'playlist': track.playlist.name if track.playlist else None
            }
            tracks_data.append(track_data)
        
        return jsonify(tracks_data)
    finally:
        db.close()

@app.route('/api/user/<int:telegram_id>/albums')
def get_user_albums(telegram_id):
    """API для получения альбомов пользователя"""
    db = DatabaseManager()
    try:
        user = db.get_or_create_user(telegram_id=telegram_id)
        albums = db.get_user_albums(user.id)
        
        albums_data = []
        for album in albums:
            tracks = db.get_album_tracks(album.id)
            album_data = {
                'id': album.id,
                'name': album.name,
                'description': album.description,
                'track_count': len(tracks),
                'tracks': [{
                    'id': track.id,
                    'title': track.title,
                    'artist': track.artist,
                    'duration': track.duration
                } for track in tracks]
            }
            albums_data.append(album_data)
        
        return jsonify(albums_data)
    finally:
        db.close()

@app.route('/api/user/<int:telegram_id>/playlists')
def get_user_playlists(telegram_id):
    """API для получения плейлистов пользователя"""
    db = DatabaseManager()
    try:
        user = db.get_or_create_user(telegram_id=telegram_id)
        playlists = db.get_user_playlists(user.id)
        
        playlists_data = []
        for playlist in playlists:
            tracks = db.get_playlist_tracks(playlist.id)
            playlist_data = {
                'id': playlist.id,
                'name': playlist.name,
                'description': playlist.description,
                'track_count': len(tracks),
                'tracks': [{
                    'id': track.id,
                    'title': track.title,
                    'artist': track.artist,
                    'duration': track.duration
                } for track in tracks]
            }
            playlists_data.append(playlist_data)
        
        return jsonify(playlists_data)
    finally:
        db.close()

@app.route('/api/track/<int:track_id>/audio')
def stream_audio(track_id):
    """Стриминг аудио файла"""
    db = DatabaseManager()
    try:
        track = db.get_track_by_id(track_id)
        if not track or not os.path.exists(track.file_path):
            return jsonify({'error': 'Трек не найден'}), 404
        
        return send_file(track.file_path, 
                        as_attachment=False,
                        download_name=f"{track.artist} - {track.title}.mp3",
                        mimetype="audio/mpeg")
    finally:
        db.close()

@app.route('/api/track/<int:track_id>', methods=['DELETE'])
def delete_track(track_id):
    """Удаление трека"""
    db = DatabaseManager()
    try:
        track = db.get_track_by_id(track_id)
        if not track:
            return jsonify({'error': 'Трек не найден'}), 404
        
        # Удаляем файл
        if os.path.exists(track.file_path):
            os.remove(track.file_path)
        
        # Удаляем из БД
        if db.delete_track(track_id):
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Ошибка удаления'}), 500
    finally:
        db.close()

@app.route('/api/album/<int:album_id>', methods=['DELETE'])
def delete_album(album_id):
    """Удаление альбома"""
    db = DatabaseManager()
    try:
        album = db.get_album_by_id(album_id)
        if not album:
            return jsonify({'error': 'Альбом не найден'}), 404
        
        # Удаляем файлы треков
        tracks = db.get_album_tracks(album_id)
        for track in tracks:
            if os.path.exists(track.file_path):
                os.remove(track.file_path)
        
        # Удаляем альбом (каскадно удалятся треки)
        if db.delete_album(album_id):
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Ошибка удаления'}), 500
    finally:
        db.close()

@app.route('/api/playlist/<int:playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    """Удаление плейлиста"""
    db = DatabaseManager()
    try:
        playlist = db.get_playlist_by_id(playlist_id)
        if not playlist:
            return jsonify({'error': 'Плейлист не найден'}), 404
        
        # Удаляем файлы треков
        tracks = db.get_playlist_tracks(playlist_id)
        for track in tracks:
            if os.path.exists(track.file_path):
                os.remove(track.file_path)
        
        # Удаляем плейлист (каскадно удалятся треки)
        if db.delete_playlist(playlist_id):
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Ошибка удаления'}), 500
    finally:
        db.close()

@app.route('/api/user/<int:telegram_id>/stats')
def get_user_stats(telegram_id):
    """Статистика пользователя"""
    db = DatabaseManager()
    try:
        user = db.get_or_create_user(telegram_id=telegram_id)
        albums = db.get_user_albums(user.id)
        playlists = db.get_user_playlists(user.id)
        tracks = db.get_all_user_tracks(user.id)
        
        total_duration = sum(track.duration for track in tracks if track.duration)
        
        stats = {
            'total_tracks': len(tracks),
            'total_albums': len(albums),
            'total_playlists': len(playlists),
            'total_duration': total_duration,
            'total_duration_formatted': format_duration(total_duration)
        }
        
        return jsonify(stats)
    finally:
        db.close()

def format_duration(seconds):
    """Форматирование длительности"""
    if not seconds:
        return "0:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

if __name__ == '__main__':
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=True)