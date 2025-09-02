from flask import render_template, request, jsonify, redirect, url_for, Blueprint
import logging
import asyncio
import json
import kookvoice
from utils import search_music, get_music_url, get_playlist, get_playlist_urls, format_playlist_data
import threading

logger = logging.getLogger(__name__)

# 全局变量
guild_data = {}  # 存储服务器信息
current_guild_id = None  # 当前选中的服务器ID

# 异步函数运行器
def run_async(coro):
    """在Flask中运行异步函数"""
    try:
        # 创建新的事件循环在线程中运行
        result = [None]
        exception = [None]
        
        def run_in_thread():
            try:
                # 创建新的事件循环
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                
                # 运行协程
                result[0] = new_loop.run_until_complete(coro)
            except Exception as e:
                exception[0] = e
            finally:
                # 清理事件循环
                try:
                    new_loop.close()
                except:
                    pass
        
        # 在新线程中运行
        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join(timeout=15)  # 15秒超时
        
        if thread.is_alive():
            # 超时处理
            logger.warning("异步函数执行超时")
            return None
            
        if exception[0]:
            raise exception[0]
        return result[0]
        
    except Exception as e:
        logger.error(f"运行异步函数异常: {e}")
        return None

def register_routes(app, bot, socketio=None):
    """注册所有路由"""
    
    @app.route('/')
    def index():
        """首页"""
        return render_template('index.html')
    
    @app.route('/dashboard')
    def dashboard():
        """控制台页面"""
        return render_template('dashboard.html')
    
    @app.route('/api/guilds', methods=['GET'])
    def get_guilds():
        """获取服务器列表"""
        try:
            # 使用同步方式调用KOOK API获取服务器列表
            try:
                import requests
                from config import BOT_TOKEN
                headers = {
                    'Authorization': f'Bot {BOT_TOKEN}',
                    'Content-Type': 'application/json'
                }
                url = 'https://www.kookapp.cn/api/v3/guild/list'
                
                logger.info(f"请求服务器列表API: {url}")
                response = requests.get(url, headers=headers, timeout=10)
                logger.info(f"服务器列表API响应状态: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"服务器列表API响应数据: {data}")
                    if data.get('code') == 0 and 'data' in data:
                        guilds = data['data'].get('items', [])
                        logger.info(f"获取到 {len(guilds)} 个服务器")
                    else:
                        guilds = []
                        logger.warning(f"服务器列表API返回错误: {data.get('message', '未知错误')}")
                else:
                    guilds = []
                    logger.error(f"服务器列表API HTTP错误: {response.status_code}")
            except Exception as e:
                logger.error(f"获取服务器列表异常: {e}")
                guilds = []
            
            # 格式化数据
            formatted_guilds = []
            for guild in guilds:
                formatted_guilds.append({
                    'id': guild.get('id', ''),
                    'name': guild.get('name', '未知服务器'),
                    'icon': guild.get('icon', ''),
                    'master_id': guild.get('master_id', '')
                })
            
            return jsonify({'success': True, 'guilds': formatted_guilds})
        except Exception as e:
            logger.error(f"获取服务器列表异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/channels', methods=['GET'])
    def get_channels():
        """获取频道列表"""
        guild_id = request.args.get('guild_id')
        if not guild_id:
            return jsonify({'success': False, 'error': '缺少guild_id参数'})
        
        try:
            # 使用同步方式调用KOOK API获取频道列表
            try:
                import requests
                from config import BOT_TOKEN
                headers = {
                    'Authorization': f'Bot {BOT_TOKEN}',
                    'Content-Type': 'application/json'
                }
                url = f'https://www.kookapp.cn/api/v3/channel/list?guild_id={guild_id}'
                
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == 0 and 'data' in data:
                        channels = data['data'].get('items', [])
                    else:
                        channels = []
                else:
                    channels = []
            except Exception as e:
                logger.error(f"获取频道列表异常: {e}")
                channels = []
            
            # 格式化数据，只返回语音频道
            formatted_channels = []
            for channel in channels:
                # 只返回语音频道 (type=2)
                if channel.get('type') == 2:
                    formatted_channels.append({
                        'id': channel.get('id', ''),
                        'name': channel.get('name', '未知频道'),
                        'type': channel.get('type', 2)
                    })
            
            return jsonify({'success': True, 'channels': formatted_channels})
        except Exception as e:
            logger.error(f"获取频道列表异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/join', methods=['POST'])
    def join_channel():
        """加入语音频道"""
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'})
            
        guild_id = data.get('guild_id')
        channel_id = data.get('channel_id')
        
        if not guild_id or not channel_id:
            return jsonify({'success': False, 'error': '缺少必要参数'})
        
        try:
            from config import BOT_TOKEN
            player = kookvoice.Player(guild_id, channel_id, BOT_TOKEN)
            player.join()
            
            # 更新全局变量
            global current_guild_id
            current_guild_id = guild_id
            
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"加入语音频道异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/leave', methods=['POST'])
    def leave_channel():
        """离开语音频道"""
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'})
            
        guild_id = data.get('guild_id')
        
        if not guild_id:
            return jsonify({'success': False, 'error': '缺少guild_id参数'})
        
        try:
            player = kookvoice.Player(guild_id)
            player.stop()
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"离开语音频道异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/search', methods=['GET'])
    def search():
        """搜索音乐"""
        keyword = request.args.get('keyword')
        if not keyword:
            return jsonify({'success': False, 'error': '缺少keyword参数'})
        
        try:
            songs = search_music(keyword)
            return jsonify({'success': True, 'songs': songs})
        except Exception as e:
            logger.error(f"搜索音乐异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/play', methods=['POST'])
    def play_music():
        """播放音乐"""
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'})
            
        guild_id = data.get('guild_id')
        channel_id = data.get('channel_id')  # 添加频道ID参数
        song_id = data.get('song_id')
        song_name = data.get('song_name', '')
        artist_name = data.get('artist_name', '')
        
        if not guild_id or not song_id:
            return jsonify({'success': False, 'error': '缺少必要参数'})
        
        try:
            # 获取音乐URL
            url = get_music_url(song_id)
            if not url:
                return jsonify({'success': False, 'error': '无法获取音乐URL'})
            
            # 播放音乐 - 提供必要的参数
            from config import BOT_TOKEN
            player = kookvoice.Player(guild_id, channel_id, BOT_TOKEN)
            player.add_music(url, {'title': song_name, 'artist': artist_name})
            
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"播放音乐异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/playlist', methods=['POST'])
    def add_playlist():
        """添加歌单"""
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'})
            
        guild_id = data.get('guild_id')
        channel_id = data.get('channel_id')  # 添加频道ID参数
        playlist_id = data.get('playlist_id')
        
        if not guild_id or not playlist_id:
            return jsonify({'success': False, 'error': '缺少必要参数'})
        
        try:
            # 获取歌单中所有歌曲
            songs = get_playlist_urls(playlist_id)
            if not songs:
                return jsonify({'success': False, 'error': '歌单为空或无法获取歌单'})
            
            # 添加到播放列表 - 提供必要的参数
            from config import BOT_TOKEN
            player = kookvoice.Player(guild_id, channel_id, BOT_TOKEN)
            for song in songs:
                player.add_music(song['marker'], {'title': song['name'], 'artist': song['artist']})
            
            return jsonify({'success': True, 'count': len(songs)})
        except Exception as e:
            logger.error(f"添加歌单异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/skip', methods=['POST'])
    def skip_music():
        """跳过当前歌曲"""
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'})
            
        guild_id = data.get('guild_id')
        
        if not guild_id:
            return jsonify({'success': False, 'error': '缺少guild_id参数'})
        
        try:
            player = kookvoice.Player(guild_id)
            player.skip()
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"跳过歌曲异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/seek', methods=['POST'])
    def seek_music():
        """跳转到指定位置"""
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'})
            
        guild_id = data.get('guild_id')
        position = data.get('position')
        
        if not guild_id or position is None:
            return jsonify({'success': False, 'error': '缺少必要参数'})
        
        try:
            player = kookvoice.Player(guild_id)
            player.seek(int(position))
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"跳转位置异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/playlist/current', methods=['GET'])
    def get_current_playlist():
        """获取当前播放列表"""
        guild_id = request.args.get('guild_id')
        
        if not guild_id:
            return jsonify({'success': False, 'error': '缺少guild_id参数'})
        
        try:
            if guild_id in kookvoice.play_list:
                playlist_data = format_playlist_data(kookvoice.play_list[guild_id])
                return jsonify({'success': True, 'playlist': playlist_data})
            else:
                return jsonify({'success': True, 'playlist': []})
        except Exception as e:
            logger.error(f"获取播放列表异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/pause', methods=['POST'])
    def pause_music():
        """暂停播放"""
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'})
            
        guild_id = data.get('guild_id')
        
        if not guild_id:
            return jsonify({'success': False, 'error': '缺少guild_id参数'})
        
        try:
            player = kookvoice.Player(guild_id)
            player.pause()
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"暂停播放异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/resume', methods=['POST'])
    def resume_music():
        """继续播放"""
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'})
            
        guild_id = data.get('guild_id')
        
        if not guild_id:
            return jsonify({'success': False, 'error': '缺少guild_id参数'})
        
        try:
            player = kookvoice.Player(guild_id)
            player.resume()
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"继续播放异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/stop', methods=['POST'])
    def stop_music():
        """停止播放"""
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'})
            
        guild_id = data.get('guild_id')
        
        if not guild_id:
            return jsonify({'success': False, 'error': '缺少guild_id参数'})
        
        try:
            player = kookvoice.Player(guild_id)
            player.stop()
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"停止播放异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/clear', methods=['POST'])
    def clear_playlist():
        """清空播放列表"""
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'})
            
        guild_id = data.get('guild_id')
        
        if not guild_id:
            return jsonify({'success': False, 'error': '缺少guild_id参数'})
        
        try:
            if guild_id in kookvoice.play_list:
                kookvoice.play_list[guild_id]['play_list'] = []
                return jsonify({'success': True})
            else:
                return jsonify({'success': True})
        except Exception as e:
            logger.error(f"清空播放列表异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/remove', methods=['POST'])
    def remove_from_playlist():
        """从播放列表中移除歌曲"""
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'})
            
        guild_id = data.get('guild_id')
        index = data.get('index')
        
        if not guild_id or index is None:
            return jsonify({'success': False, 'error': '缺少必要参数'})
        
        try:
            if guild_id in kookvoice.play_list:
                playlist = kookvoice.play_list[guild_id]['play_list']
                if 0 <= int(index) < len(playlist):
                    playlist.pop(int(index))
                    return jsonify({'success': True})
                else:
                    return jsonify({'success': False, 'error': '索引超出范围'})
            else:
                return jsonify({'success': False, 'error': '播放列表不存在'})
        except Exception as e:
            logger.error(f"移除歌曲异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    # 如果SocketIO可用，注册SocketIO事件
    if socketio:
        @socketio.on('connect')
        def handle_connect():
            logger.info('客户端已连接')
        
        @socketio.on('disconnect')
        def handle_disconnect():
            logger.info('客户端已断开连接')
        
        @socketio.on('join_room')
        def handle_join_room(data):
            guild_id = data.get('guild_id')
            if guild_id:
                socketio.join_room(guild_id)
                logger.info(f'客户端加入房间: {guild_id}')
        
        @socketio.on('leave_room')
        def handle_leave_room(data):
            guild_id = data.get('guild_id')
            if guild_id:
                socketio.leave_room(guild_id)
                logger.info(f'客户端离开房间: {guild_id}')

# 辅助函数
async def get_guild_list(bot):
    """获取服务器列表"""
    try:
        guilds = await bot.client.gate.request('GET', 'guild/list')
        if guilds and "items" in guilds:
            return guilds["items"]
        return []
    except Exception as e:
        logger.error(f"获取服务器列表异常: {e}")
        return []

async def get_channel_list(bot, guild_id):
    """获取频道列表"""
    try:
        channels = await bot.client.gate.request('GET', 'channel/list', params={'guild_id': guild_id})
        if channels and "items" in channels:
            # 过滤出语音频道
            voice_channels = [c for c in channels["items"] if c.get('type') == 2]
            return voice_channels
        return []
    except Exception as e:
        logger.error(f"获取频道列表异常: {e}")
        return []