from flask import Blueprint, jsonify, request
import logging
import os
import sys
from .kookvoice import kookvoice
from .utils import format_playlist_data

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取系统统计数据"""
    try:
        # 获取活跃服务器数
        active_guilds = len(kookvoice.play_list)
        
        # 获取播放中的歌曲数
        playing_songs = 0
        queued_songs = 0
        
        for guild_id, guild_data in kookvoice.play_list.items():
            if guild_data.get('now_playing'):
                playing_songs += 1
            queued_songs += len(guild_data.get('play_list', []))
        
        # 检查机器人状态
        bot_status = 'online'  # 假设机器人在线
        
        # 检查API状态
        api_status = 'normal'  # 假设API正常
        
        # 检查FFMPEG状态
        from .config import FFMPEG_PATH
        ffmpeg_status = 'normal' if os.path.exists(FFMPEG_PATH) else 'error'
        
        return jsonify({
            'active_guilds': active_guilds,
            'playing_songs': playing_songs,
            'queued_songs': queued_songs,
            'bot_status': bot_status,
            'api_status': api_status,
            'ffmpeg_status': ffmpeg_status
        })
    except Exception as e:
        logger.error(f"获取统计数据异常: {e}")
        return jsonify({
            'active_guilds': 0,
            'playing_songs': 0,
            'queued_songs': 0,
            'bot_status': 'error',
            'api_status': 'error',
            'ffmpeg_status': 'error'
        })