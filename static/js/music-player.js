// Глобальные переменные
let currentTrack = null;
let currentPlaylist = [];
let currentIndex = 0;
let isPlaying = false;
let isShuffled = false;
let originalPlaylist = [];
let audioPlayer = null;
let telegramId = null;

// Инициализация плеера
function initializeMusicPlayer(userId) {
    telegramId = userId;
    audioPlayer = document.getElementById('audio-player');
    
    if (!audioPlayer) {
        console.error('Audio player element not found');
        return;
    }
    
    // Настройка событий аудио плеера
    audioPlayer.addEventListener('loadstart', onAudioLoadStart);
    audioPlayer.addEventListener('canplay', onAudioCanPlay);
    audioPlayer.addEventListener('timeupdate', onTimeUpdate);
    audioPlayer.addEventListener('ended', onTrackEnded);
    audioPlayer.addEventListener('error', onAudioError);
    
    // Настройка громкости
    const volumeSlider = document.getElementById('volume-slider');
    if (volumeSlider) {
        volumeSlider.addEventListener('input', setVolume);
        audioPlayer.volume = volumeSlider.value / 100;
    }
    
    // Настройка клика по прогресс-бару
    const progressBar = document.getElementById('progress-bar');
    if (progressBar && progressBar.parentElement) {
        progressBar.parentElement.addEventListener('click', seekTo);
    }
    
    // Загружаем все треки пользователя
    loadAllTracks();
}

// Загрузка всех треков
async function loadAllTracks() {
    try {
        const response = await fetch(`/api/user/${telegramId}/tracks`);
        const tracks = await response.json();
        
        if (Array.isArray(tracks)) {
            currentPlaylist = tracks;
            originalPlaylist = [...tracks];
        }
    } catch (error) {
        console.error('Ошибка загрузки треков:', error);
        showToast('Ошибка загрузки треков', 'error');
    }
}

// Загрузка статистики пользователя
async function loadUserStats() {
    try {
        const response = await fetch(`/api/user/${telegramId}/stats`);
        const stats = await response.json();
        
        document.getElementById('stats-tracks').textContent = stats.total_tracks || 0;
        document.getElementById('stats-albums').textContent = stats.total_albums || 0;
        document.getElementById('stats-playlists').textContent = stats.total_playlists || 0;
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
    }
}

// Воспроизведение трека
async function playTrack(trackId) {
    const track = currentPlaylist.find(t => t.id === trackId);
    if (!track) {
        showToast('Трек не найден', 'error');
        return;
    }
    
    // Останавливаем текущий трек
    if (audioPlayer) {
        audioPlayer.pause();
    }
    
    currentTrack = track;
    currentIndex = currentPlaylist.findIndex(t => t.id === trackId);
    
    // Обновляем UI
    updateTrackInfo();
    updatePlayButton(false);
    
    // Загружаем и воспроизводим
    try {
        audioPlayer.src = `/api/track/${trackId}/audio`;
        await audioPlayer.play();
        isPlaying = true;
        updatePlayButton(true);
        highlightCurrentTrack();
        showToast(`Воспроизводится: ${track.artist} - ${track.title}`, 'success');
    } catch (error) {
        console.error('Ошибка воспроизведения:', error);
        showToast('Ошибка воспроизведения трека', 'error');
        isPlaying = false;
        updatePlayButton(false);
    }
}

// Переключение воспроизведения/паузы
function togglePlayPause() {
    if (!audioPlayer || !currentTrack) {
        if (currentPlaylist.length > 0) {
            playTrack(currentPlaylist[0].id);
        } else {
            showToast('Нет треков для воспроизведения', 'warning');
        }
        return;
    }
    
    if (isPlaying) {
        audioPlayer.pause();
        isPlaying = false;
        updatePlayButton(false);
    } else {
        audioPlayer.play().then(() => {
            isPlaying = true;
            updatePlayButton(true);
        }).catch(error => {
            console.error('Ошибка воспроизведения:', error);
            showToast('Ошибка воспроизведения', 'error');
        });
    }
}

// Предыдущий трек
function previousTrack() {
    if (currentPlaylist.length === 0) return;
    
    let newIndex = currentIndex - 1;
    if (newIndex < 0) {
        newIndex = currentPlaylist.length - 1;
    }
    
    currentIndex = newIndex;
    playTrack(currentPlaylist[currentIndex].id);
}

// Следующий трек
function nextTrack() {
    if (currentPlaylist.length === 0) return;
    
    let newIndex = currentIndex + 1;
    if (newIndex >= currentPlaylist.length) {
        newIndex = 0;
    }
    
    currentIndex = newIndex;
    playTrack(currentPlaylist[currentIndex].id);
}

// Перемешивание
function toggleShuffle() {
    isShuffled = !isShuffled;
    const shuffleIcon = document.getElementById('shuffle-icon');
    const shuffleBtn = shuffleIcon.parentElement;
    
    if (isShuffled) {
        // Перемешиваем плейлист
        currentPlaylist = shuffleArray([...originalPlaylist]);
        
        // Находим текущий трек в новом порядке
        if (currentTrack) {
            currentIndex = currentPlaylist.findIndex(t => t.id === currentTrack.id);
        }
        
        shuffleBtn.classList.add('btn-shuffle-active');
        showToast('Перемешивание включено', 'info');
    } else {
        // Восстанавливаем оригинальный порядок
        currentPlaylist = [...originalPlaylist];
        
        // Находим текущий трек в оригинальном порядке
        if (currentTrack) {
            currentIndex = currentPlaylist.findIndex(t => t.id === currentTrack.id);
        }
        
        shuffleBtn.classList.remove('btn-shuffle-active');
        showToast('Перемешивание выключено', 'info');
    }
}

// Воспроизвести все треки
function playAllTracks() {
    if (currentPlaylist.length === 0) {
        showToast('Нет треков для воспроизведения', 'warning');
        return;
    }
    
    currentIndex = 0;
    playTrack(currentPlaylist[0].id);
}

// Перемешать все треки
function shuffleAllTracks() {
    if (!isShuffled) {
        toggleShuffle();
    }
    playAllTracks();
}

// Воспроизведение альбома
async function playAlbum(albumId) {
    try {
        const response = await fetch(`/api/user/${telegramId}/albums`);
        const albums = await response.json();
        const album = albums.find(a => a.id === albumId);
        
        if (album && album.tracks.length > 0) {
            currentPlaylist = album.tracks;
            originalPlaylist = [...album.tracks];
            isShuffled = false;
            
            // Сбрасываем состояние перемешивания
            const shuffleBtn = document.querySelector('#shuffle-icon').parentElement;
            shuffleBtn.classList.remove('btn-shuffle-active');
            
            currentIndex = 0;
            playTrack(album.tracks[0].id);
            
            showToast(`Воспроизводится альбом: ${album.name}`, 'success');
        }
    } catch (error) {
        console.error('Ошибка загрузки альбома:', error);
        showToast('Ошибка загрузки альбома', 'error');
    }
}

// Воспроизведение плейлиста
async function playPlaylist(playlistId) {
    try {
        const response = await fetch(`/api/user/${telegramId}/playlists`);
        const playlists = await response.json();
        const playlist = playlists.find(p => p.id === playlistId);
        
        if (playlist && playlist.tracks.length > 0) {
            currentPlaylist = playlist.tracks;
            originalPlaylist = [...playlist.tracks];
            isShuffled = false;
            
            // Сбрасываем состояние перемешивания
            const shuffleBtn = document.querySelector('#shuffle-icon').parentElement;
            shuffleBtn.classList.remove('btn-shuffle-active');
            
            currentIndex = 0;
            playTrack(playlist.tracks[0].id);
            
            showToast(`Воспроизводится плейлист: ${playlist.name}`, 'success');
        }
    } catch (error) {
        console.error('Ошибка загрузки плейлиста:', error);
        showToast('Ошибка загрузки плейлиста', 'error');
    }
}

// Установка громкости
function setVolume(event) {
    if (audioPlayer) {
        audioPlayer.volume = event.target.value / 100;
    }
}

// Перемотка
function seekTo(event) {
    if (!audioPlayer || !audioPlayer.duration) return;
    
    const progressContainer = event.currentTarget;
    const clickX = event.offsetX;
    const width = progressContainer.offsetWidth;
    const newTime = (clickX / width) * audioPlayer.duration;
    
    audioPlayer.currentTime = newTime;
}

// Удаление трека
async function deleteTrack(trackId) {
    if (!confirm('Вы уверены, что хотите удалить этот трек?')) return;
    
    try {
        const response = await fetch(`/api/track/${trackId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Удаляем из DOM
            const trackRow = document.querySelector(`tr[data-track-id="${trackId}"]`);
            if (trackRow) {
                trackRow.remove();
            }
            
            // Удаляем из плейлистов
            currentPlaylist = currentPlaylist.filter(t => t.id !== trackId);
            originalPlaylist = originalPlaylist.filter(t => t.id !== trackId);
            
            // Если удаляемый трек воспроизводится, останавливаем
            if (currentTrack && currentTrack.id === trackId) {
                audioPlayer.pause();
                currentTrack = null;
                isPlaying = false;
                updatePlayButton(false);
                updateTrackInfo();
            }
            
            showToast('Трек удален', 'success');
            loadUserStats();
        } else {
            throw new Error('Ошибка удаления');
        }
    } catch (error) {
        console.error('Ошибка удаления трека:', error);
        showToast('Ошибка удаления трека', 'error');
    }
}

// Удаление альбома
async function deleteAlbum(albumId) {
    if (!confirm('Вы уверены, что хотите удалить этот альбом? Все треки в нем будут удалены.')) return;
    
    try {
        const response = await fetch(`/api/album/${albumId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Удаляем из DOM
            const albumCard = document.querySelector(`div[data-album-id="${albumId}"]`);
            if (albumCard) {
                albumCard.remove();
            }
            
            showToast('Альбом удален', 'success');
            loadUserStats();
            loadAllTracks(); // Перезагружаем треки
        } else {
            throw new Error('Ошибка удаления');
        }
    } catch (error) {
        console.error('Ошибка удаления альбома:', error);
        showToast('Ошибка удаления альбома', 'error');
    }
}

// Удаление плейлиста
async function deletePlaylist(playlistId) {
    if (!confirm('Вы уверены, что хотите удалить этот плейлист? Все треки в нем будут удалены.')) return;
    
    try {
        const response = await fetch(`/api/playlist/${playlistId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Удаляем из DOM
            const playlistCard = document.querySelector(`div[data-playlist-id="${playlistId}"]`);
            if (playlistCard) {
                playlistCard.remove();
            }
            
            showToast('Плейлист удален', 'success');
            loadUserStats();
            loadAllTracks(); // Перезагружаем треки
        } else {
            throw new Error('Ошибка удаления');
        }
    } catch (error) {
        console.error('Ошибка удаления плейлиста:', error);
        showToast('Ошибка удаления плейлиста', 'error');
    }
}

// Переключение секций
function showSection(sectionName) {
    // Скрываем все секции
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.add('d-none');
    });
    
    // Показываем нужную секцию
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (targetSection) {
        targetSection.classList.remove('d-none');
    }
    
    // Обновляем активную навигацию
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    event.target.classList.add('active');
}

// События аудио плеера
function onAudioLoadStart() {
    const playBtn = document.getElementById('play-pause-btn');
    if (playBtn) {
        playBtn.innerHTML = '<div class="loading"></div>';
    }
}

function onAudioCanPlay() {
    updatePlayButton(isPlaying);
}

function onTimeUpdate() {
    if (!audioPlayer) return;
    
    const currentTime = audioPlayer.currentTime;
    const duration = audioPlayer.duration;
    
    if (duration) {
        const progress = (currentTime / duration) * 100;
        const progressBar = document.getElementById('progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        // Обновляем время
        const currentTimeEl = document.getElementById('current-time');
        const totalTimeEl = document.getElementById('total-time');
        
        if (currentTimeEl) {
            currentTimeEl.textContent = formatTime(currentTime);
        }
        
        if (totalTimeEl) {
            totalTimeEl.textContent = formatTime(duration);
        }
    }
}

function onTrackEnded() {
    // Автоматически переходим к следующему треку
    nextTrack();
}

function onAudioError(event) {
    console.error('Ошибка аудио:', event);
    showToast('Ошибка загрузки аудио файла', 'error');
    isPlaying = false;
    updatePlayButton(false);
}

// Вспомогательные функции
function updateTrackInfo() {
    const titleEl = document.getElementById('current-track-title');
    const artistEl = document.getElementById('current-track-artist');
    
    if (currentTrack) {
        if (titleEl) titleEl.textContent = currentTrack.title;
        if (artistEl) artistEl.textContent = currentTrack.artist;
    } else {
        if (titleEl) titleEl.textContent = 'Выберите трек';
        if (artistEl) artistEl.textContent = 'для воспроизведения';
    }
}

function updatePlayButton(playing) {
    const playBtn = document.getElementById('play-pause-btn');
    if (playBtn) {
        const icon = playing ? 'fas fa-pause' : 'fas fa-play';
        playBtn.innerHTML = `<i class="${icon}"></i>`;
        
        if (playing) {
            playBtn.classList.add('btn-playing');
        } else {
            playBtn.classList.remove('btn-playing');
        }
    }
}

function highlightCurrentTrack() {
    // Снимаем подсветку с всех треков
    document.querySelectorAll('tr[data-track-id]').forEach(row => {
        row.classList.remove('track-playing');
    });
    
    // Подсвечиваем текущий трек
    if (currentTrack) {
        const currentRow = document.querySelector(`tr[data-track-id="${currentTrack.id}"]`);
        if (currentRow) {
            currentRow.classList.add('track-playing');
        }
    }
}

function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '0:00';
    
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

function showToast(message, type = 'info') {
    // Создаем контейнер для тостов если его нет
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Определяем цвет по типу
    const colors = {
        success: 'text-bg-success',
        error: 'text-bg-danger',
        warning: 'text-bg-warning',
        info: 'text-bg-info'
    };
    
    // Создаем тост
    const toast = document.createElement('div');
    toast.className = `toast align-items-center ${colors[type] || colors.info} border-0`;
    toast.setAttribute('role', 'alert');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Показываем тост
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 3000
    });
    bsToast.show();
    
    // Удаляем элемент после скрытия
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}