import requests
import logging
import json
import os
from config import MUSIC_API_BASE, BACKUP_MUSIC_API

logger = logging.getLogger(__name__)

COOKIE_TXT_PATH = os.path.join(os.path.dirname(__file__), "Cookie", "cookie.txt")


def load_cookie_header():
    try:
        if os.path.exists(COOKIE_TXT_PATH):
            with open(COOKIE_TXT_PATH, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return ""


def build_headers(extra: dict | None = None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127 Safari/537.36",
    }
    cookie_str = load_cookie_header()
    if cookie_str:
        headers["Cookie"] = cookie_str
    if extra:
        headers.update(extra)
    return headers

# 搜索音乐
def search_music(keyword):
    try:
        res = requests.get(f"{MUSIC_API_BASE}/cloudsearch?keywords={keyword}", headers=build_headers())
        data = res.json()
        songs = data.get('result', {}).get('songs', [])
        return songs
    except Exception as e:
        logger.error(f"搜索音乐异常: {e}")
        try:
            # 尝试使用备用API
            res = requests.get(f"{BACKUP_MUSIC_API}/search?keywords={keyword}", headers=build_headers())
            data = res.json()
            songs = data.get('result', {}).get('songs', [])
            return songs
        except Exception as e2:
            logger.error(f"备用API搜索音乐异常: {e2}")
            return []

# 获取音乐URL
def get_music_url(song_id):
    try:
        res = requests.get(f"{MUSIC_API_BASE}/song/url?id={song_id}", headers=build_headers())
        data = res.json()
        url = data.get('data', [{}])[0].get('url', '')
        return url
    except Exception as e:
        logger.error(f"获取音乐URL异常: {e}")
        try:
            # 尝试使用备用API
            res = requests.get(f"{BACKUP_MUSIC_API}/song/url?id={song_id}", headers=build_headers())
            data = res.json()
            url = data.get('data', [{}])[0].get('url', '')
            return url
        except Exception as e2:
            logger.error(f"备用API获取音乐URL异常: {e2}")
            return ''

# 获取歌单
def get_playlist(playlist_id):
    try:
        res = requests.get(f"{MUSIC_API_BASE}/playlist/detail?id={playlist_id}", headers=build_headers())
        data = res.json()
        return data.get('playlist', {})
    except Exception as e:
        logger.error(f"获取歌单异常: {e}")
        try:
            # 尝试使用备用API
            res = requests.get(f"{BACKUP_MUSIC_API}/playlist/detail?id={playlist_id}", headers=build_headers())
            data = res.json()
            return data.get('playlist', {})
        except Exception as e2:
            logger.error(f"备用API获取歌单异常: {e2}")
            return {}

# 获取歌单中所有歌曲（支持分页）
def get_playlist_all_tracks(playlist_id):
    """获取歌单中所有歌曲，支持分页"""
    try:
        # 首先获取歌单基本信息
        playlist = get_playlist(playlist_id)
        if not playlist:
            return []
        
        track_count = playlist.get('trackCount', 0)
        print(f"歌单总歌曲数: {track_count}")
        
        all_tracks = []
        limit = 1000  # 每次请求的最大数量
        offset = 0
        
        while offset < track_count:
            try:
                # 使用分页参数获取歌曲 - 只获取歌曲信息，不获取URL
                url = f"{MUSIC_API_BASE}/playlist/track/all?id={playlist_id}&limit={limit}&offset={offset}"
                print(f"请求分页: offset={offset}, limit={limit}")
                
                res = requests.get(url, timeout=10, headers=build_headers())
                if res.status_code == 200:
                    data = res.json()
                    tracks = data.get('songs', [])
                    
                    if not tracks:
                        break
                    
                    all_tracks.extend(tracks)
                    print(f"获取到 {len(tracks)} 首歌曲")
                    
                    if len(tracks) < limit:
                        break
                    
                    offset += limit
                else:
                    print(f"分页请求失败: {res.status_code}")
                    break
                    
            except Exception as e:
                print(f"分页请求异常: {e}")
                break
        
        print(f"总共获取到 {len(all_tracks)} 首歌曲")
        return all_tracks
        
    except Exception as e:
        logger.error(f"获取完整歌单异常: {e}")
        return []

# 获取歌单中所有歌曲信息（不获取URL）
def get_playlist_urls(playlist_id):
    """获取歌单中所有歌曲信息，使用.env中配置的API，不获取URL"""
    # 使用分页功能获取所有歌曲
    tracks = get_playlist_all_tracks(playlist_id)
    result = []
    
    print(f"处理 {len(tracks)} 首歌曲...")
    
    for track in tracks:
        song_id = track.get('id')
        song_name = track.get('name', '')
        artists = track.get('ar', [])
        artist_name = artists[0].get('name', '') if artists else ''
        
        # 创建歌单歌曲标记，稍后实时获取URL
        song_marker = f"PLAYLIST_SONG:{song_id}:{song_name}:{artist_name}"
        
        result.append({
            'id': song_id,
            'name': song_name,
            'artist': artist_name,
            'marker': song_marker
        })
    
    print(f"成功处理 {len(result)} 首歌曲")
    return result

# 格式化播放列表数据
def format_playlist_data(play_list_data):
    result = []
    
    # 处理当前播放的歌曲
    now_playing = play_list_data.get('now_playing')
    if now_playing:
        file_path = now_playing.get('file', '')
        extra_data = now_playing.get('extra', {})
        
        # 检查是否是歌单歌曲标记
        if file_path.startswith("PLAYLIST_SONG:"):
            parts = file_path.split(":")
            if len(parts) >= 4:
                song_id = parts[1]
                song_name = parts[2]
                artist_name = parts[3]
                
                result.append({
                    'id': song_id,
                    'name': song_name,
                    'artist': artist_name,
                    'duration': now_playing.get('duration', 0),
                    'playing': True,
                    'position': now_playing.get('ss', 0),
                    'start_time': now_playing.get('start', 0)
                })
        else:
            # 普通文件
            file_name = file_path.split('/')[-1] if '/' in file_path else file_path
            result.append({
                'id': 'local',
                'name': extra_data.get('title', file_name),
                'artist': extra_data.get('artist', '本地文件'),
                'playing': True,
                'position': now_playing.get('ss', 0),
                'start_time': now_playing.get('start', 0)
            })
    
    # 处理播放列表中的歌曲
    play_list = play_list_data.get('play_list', [])
    for queue_index, item in enumerate(play_list):
        file_path = item.get('file', '')
        extra_data = item.get('extra', {})
        
        # 检查是否是歌单歌曲标记
        if file_path.startswith("PLAYLIST_SONG:"):
            parts = file_path.split(":")
            if len(parts) >= 4:
                song_id = parts[1]
                song_name = parts[2]
                artist_name = parts[3]
                
                result.append({
                    'id': song_id,
                    'name': song_name,
                    'artist': artist_name,
                    'duration': 0,
                    'queue_index': queue_index,
                    'playing': False
                })
        else:
            # 普通文件
            file_name = file_path.split('/')[-1] if '/' in file_path else file_path
            result.append({
                'id': 'local',
                'name': extra_data.get('title', file_name),
                'artist': extra_data.get('artist', '本地文件'),
                'queue_index': queue_index,
                'playing': False
            })
    
    return result

# 保存配置到文件
def save_config(config_data, file_path='config.json'):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存配置异常: {e}")
        return False

# 从文件加载配置
def load_config(file_path='config.json'):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置异常: {e}")
        return {}