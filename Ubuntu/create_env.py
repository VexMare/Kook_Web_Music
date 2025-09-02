#!/usr/bin/env python3
# -*- coding: utf-8 -*-

env_content = """# KOOK机器人配置
BOT_TOKEN=1/Mzg0MjE=/O02aee6F14ixnJfYns4AuA==

# FFMPEG配置
FFMPEG_PATH=./ffmpeg/bin/ffmpeg.exe
FFPROBE_PATH=./ffmpeg/bin/ffprobe.exe

# 音乐API配置
MUSIC_API_BASE=https://1304404172-f3na0r58ws.ap-beijing.tencentscf.com

# Web控制台配置
SECRET_KEY=kook_web_music_secret_key
HOST=0.0.0.0
PORT=5000
DEBUG=True
"""

with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print("✅ .env文件创建成功！")
