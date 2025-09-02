import os

# 基本配置
DEBUG = False
HOST = "0.0.0.0"
PORT = 5000

# KOOK机器人配置
BOT_TOKEN = os.environ.get("BOT_TOKEN", "1/Mzg0MjE=/O02aee6F14ixnJfYns4AuA==")

# FFMPEG配置 - 使用相对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
FFMPEG_PATH = os.environ.get("FFMPEG_PATH", os.path.join(current_dir, "ffmpeg", "bin", "ffmpeg.exe"))
FFPROBE_PATH = os.environ.get("FFPROBE_PATH", os.path.join(current_dir, "ffmpeg", "bin", "ffprobe.exe"))

# 音乐API配置
MUSIC_API_BASE = os.environ.get("MUSIC_API_BASE", "https://1304404172-f3na0r58ws.ap-beijing.tencentscf.com")

# 备用API地址
BACKUP_MUSIC_API = "https://api.music.liuzhijin.cn"

# Web控制台配置
SECRET_KEY = os.environ.get("SECRET_KEY", "kook_web_music_secret_key")