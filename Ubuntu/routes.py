from flask import render_template, request, jsonify, redirect, url_for, Blueprint
import logging
import asyncio
import json
import time
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
    
    @app.route('/monitor')
    def monitor():
        """监控页面"""
        return render_template('monitor.html')
    
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
    
    @app.route('/api/system/status', methods=['GET'])
    def get_system_status():
        """获取系统状态信息"""
        try:
            import psutil
            import os
            import time
            
            # 获取系统资源信息
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 获取进程信息
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            # 获取网络信息
            network = psutil.net_io_counters()
            
            # 获取音频缓存信息
            from kookvoice.kookvoice import audio_cache, cache_max_size, get_cleanup_stats
            cache_count = len(audio_cache)
            cache_size = sum(cache_data.get('size', 0) for cache_data in audio_cache.values())
            cleanup_stats = get_cleanup_stats()
            
            # 调试信息：记录缓存状态
            logger.debug(f'缓存统计 - 数量: {cache_count}, 大小: {cache_size} bytes, 缓存键: {list(audio_cache.keys())}')
            
            # 获取播放状态
            active_guilds = len(kookvoice.play_list)
            playing_songs = 0
            queued_songs = 0
            
            for guild_data in kookvoice.play_list.values():
                if guild_data.get('now_playing'):
                    playing_songs += 1
                queued_songs += len(guild_data.get('play_list', []))
            
            return jsonify({
                'success': True,
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory': {
                        'total': memory.total,
                        'available': memory.available,
                        'percent': memory.percent,
                        'used': memory.used
                    },
                    'disk': {
                        'total': disk.total,
                        'used': disk.used,
                        'free': disk.free,
                        'percent': (disk.used / disk.total) * 100
                    },
                    'network': {
                        'bytes_sent': network.bytes_sent,
                        'bytes_recv': network.bytes_recv,
                        'packets_sent': network.packets_sent,
                        'packets_recv': network.packets_recv
                    }
                },
                'process': {
                    'pid': process.pid,
                    'memory_rss': process_memory.rss,
                    'memory_vms': process_memory.vms,
                    'cpu_percent': process_cpu,
                    'create_time': process.create_time(),
                    'uptime': time.time() - process.create_time()
                },
                'audio_cache': {
                    'count': cache_count,
                    'max_size': cache_max_size,
                    'total_size': cache_size,
                    'size_mb': cache_size / 1024 / 1024
                },
                'cleanup_stats': cleanup_stats,
                'playback': {
                    'active_guilds': active_guilds,
                    'playing_songs': playing_songs,
                    'queued_songs': queued_songs
                },
                'timestamp': time.time()
            })
        except Exception as e:
            logger.error(f"获取系统状态异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/logs', methods=['GET'])
    def get_logs():
        """获取日志信息"""
        try:
            import os
            lines = request.args.get('lines', 100, type=int)
            log_type = request.args.get('type', 'app', type=str)
            
            # 确定日志文件路径
            if log_type == 'app':
                log_file = 'app.log'
            elif log_type == 'debug':
                log_file = 'debug.log'
            else:
                return jsonify({'success': False, 'error': '无效的日志类型'})
            
            # 读取日志文件
            if not os.path.exists(log_file):
                return jsonify({'success': False, 'error': '日志文件不存在'})
            
            # 读取最后N行
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            # 解析日志行
            logs = []
            for line in recent_lines:
                line = line.strip()
                if line:
                    # 简单的日志解析
                    if ' - ' in line:
                        parts = line.split(' - ', 2)
                        if len(parts) >= 3:
                            timestamp = parts[0]
                            level = parts[1]
                            message = parts[2]
                            
                            # 确定日志级别
                            if 'ERROR' in level:
                                log_level = 'error'
                            elif 'WARNING' in level:
                                log_level = 'warning'
                            elif 'INFO' in level:
                                log_level = 'info'
                            elif 'DEBUG' in level:
                                log_level = 'debug'
                            else:
                                log_level = 'info'
                            
                            logs.append({
                                'timestamp': timestamp,
                                'level': log_level,
                                'message': message,
                                'raw': line
                            })
                        else:
                            logs.append({
                                'timestamp': '',
                                'level': 'info',
                                'message': line,
                                'raw': line
                            })
                    else:
                        logs.append({
                            'timestamp': '',
                            'level': 'info',
                            'message': line,
                            'raw': line
                        })
            
            return jsonify({
                'success': True,
                'logs': logs,
                'total_lines': len(all_lines),
                'returned_lines': len(logs),
                'log_type': log_type
            })
            
        except Exception as e:
            logger.error(f"获取日志异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/logs/clear', methods=['POST'])
    def clear_logs():
        """清空日志文件"""
        try:
            log_type = request.json.get('type', 'app') if request.json else 'app'
            
            if log_type == 'app':
                log_file = 'app.log'
            elif log_type == 'debug':
                log_file = 'debug.log'
            else:
                return jsonify({'success': False, 'error': '无效的日志类型'})
            
            # 清空日志文件
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('')
            
            return jsonify({'success': True, 'message': f'{log_type}日志已清空'})
            
        except Exception as e:
            logger.error(f"清空日志异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/system/cleanup', methods=['POST'])
    def manual_cleanup():
        """手动清理缓存和内存"""
        try:
            import psutil
            from kookvoice.kookvoice import audio_cache, song_play_count, cleanup_audio_cache, gc, cache_max_size
            
            # 记录清理前的状态
            cache_before = len(audio_cache)
            memory_before = psutil.Process().memory_info()
            
            # 手动清理：清空所有音频缓存
            audio_cache.clear()
            
            # 记录清理后的状态
            cache_after = len(audio_cache)
            cache_cleared = cache_before - cache_after
            
            # 重置播放计数
            song_play_count.clear()
            
            # 强制垃圾回收
            gc.collect()
            
            # 记录清理后的状态
            memory_after = psutil.Process().memory_info()
            memory_freed = (memory_before.rss - memory_after.rss) / 1024 / 1024
            
            return jsonify({
                'success': True,
                'message': '手动清理完成',
                'details': {
                    'cache_cleared': cache_cleared,
                    'cache_before': cache_before,
                    'cache_after': cache_after,
                    'memory_freed_mb': round(memory_freed, 2),
                    'memory_before_mb': round(memory_before.rss / 1024 / 1024, 2),
                    'memory_after_mb': round(memory_after.rss / 1024 / 1024, 2)
                }
            })
            
        except Exception as e:
            logger.error(f"手动清理异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/system/cleanup/config', methods=['POST'])
    def update_cleanup_config():
        """更新清理配置"""
        try:
            from kookvoice.kookvoice import cleanup_threshold
            
            data = request.json
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'})
            
            new_threshold = data.get('threshold')
            if new_threshold is not None:
                if not isinstance(new_threshold, int) or new_threshold < 1 or new_threshold > 10:
                    return jsonify({'success': False, 'error': '清理阈值必须在1-10之间'})
                
                # 更新全局变量
                import kookvoice.kookvoice
                kookvoice.kookvoice.cleanup_threshold = new_threshold
                
                return jsonify({
                    'success': True,
                    'message': f'清理阈值已更新为 {new_threshold} 首歌曲',
                    'new_threshold': new_threshold
                })
            else:
                return jsonify({'success': False, 'error': '缺少threshold参数'})
                
        except Exception as e:
            logger.error(f"更新清理配置异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/terminal/output', methods=['GET'])
    def get_terminal_output():
        """获取终端输出"""
        try:
            import subprocess
            import os
            
            # 获取请求参数
            last_position = request.args.get('last_position', 0, type=int)
            
            # 获取最新的终端输出
            log_file = 'app.log'
            if os.path.exists(log_file):
                # 获取文件大小
                file_size = os.path.getsize(log_file)
                
                # 如果文件大小小于上次位置，说明文件被清空了
                if file_size < last_position:
                    last_position = 0
                
                # 只读取新增的内容
                if file_size > last_position:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(last_position)
                        output = f.read()
                else:
                    output = ""
                
                # 调试信息
                logger.debug(f'终端输出API - 文件大小: {file_size}, 上次位置: {last_position}, 新内容长度: {len(output)}')
                    
                return jsonify({
                    'success': True,
                    'output': output,
                    'timestamp': time.time(),
                    'file_size': file_size,
                    'last_position': last_position
                })
            else:
                return jsonify({
                    'success': True,
                    'output': '日志文件不存在',
                    'timestamp': time.time(),
                    'file_size': 0,
                    'last_position': 0
                })
                
        except Exception as e:
            logger.error(f"获取终端输出异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/terminal/command', methods=['POST'])
    def execute_terminal_command():
        """执行终端命令"""
        try:
            data = request.json
            if not data or 'command' not in data:
                return jsonify({'success': False, 'error': '缺少命令参数'})
            
            command = data['command']
            
            # 安全检查：只允许特定的安全命令
            allowed_commands = [
                'ps', 'top', 'htop', 'df', 'free', 'uptime', 'whoami',
                'pwd', 'ls', 'cat', 'tail', 'head', 'grep', 'find'
            ]
            
            command_base = command.split()[0] if command.split() else ''
            if command_base not in allowed_commands:
                return jsonify({'success': False, 'error': f'不允许执行命令: {command_base}'})
            
            # 执行命令
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return jsonify({
                'success': True,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'command': command
            })
            
        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'error': '命令执行超时'})
        except Exception as e:
            logger.error(f"执行终端命令异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
    

    
    @app.route('/api/cache/test', methods=['POST'])
    def test_cache():
        """测试缓存功能"""
        try:
            from kookvoice.kookvoice import audio_cache
            import threading
            
            # 创建一个测试音频文件
            test_file = "test_audio.mp3"
            
            # 在后台线程中预加载测试文件
            def run_test_preload():
                try:
                    cache_key = f"{test_file}:0"
                    if cache_key not in audio_cache:
                        # 模拟预加载过程
                        audio_cache[cache_key] = {
                            'data': b'test_audio_data_' + str(time.time()).encode(),
                            'timestamp': time.time(),
                            'size': 1024 * 1024  # 1MB
                        }
                        logger.info(f'测试缓存添加成功: {cache_key}')
                    else:
                        logger.info(f'测试缓存已存在: {cache_key}')
                except Exception as e:
                    logger.error(f'测试缓存失败: {e}')
            
            # 启动测试线程
            test_thread = threading.Thread(target=run_test_preload)
            test_thread.daemon = True
            test_thread.start()
            
            return jsonify({
                'success': True,
                'message': '测试缓存已启动',
                'cache_count': len(audio_cache)
            })
            
        except Exception as e:
            logger.error(f"测试缓存异常: {e}")
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