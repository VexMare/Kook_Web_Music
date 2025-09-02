// 全局变量
let currentGuildId = null;
let currentGuildName = null;
let currentChannelId = null;
let socket = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，开始初始化...');
    initializeApp();
});

// 初始化应用
function initializeApp() {
    // 绑定事件
    bindEvents();
    
    // 加载服务器列表
    loadGuilds();
    

    
    // 初始化Socket.IO（如果可用）
    initializeSocketIO();
    
    // 定期刷新状态
    setInterval(() => {
        if (currentGuildId) {
            loadPlaylist(currentGuildId);
        }
    }, 5000);

    // 恢复上次选择的服务器与频道
    try {
        const savedGuildId = localStorage.getItem('currentGuildId');
        const savedGuildName = localStorage.getItem('currentGuildName');
        const savedChannelId = localStorage.getItem('currentChannelId');
        if (savedGuildId && savedGuildName) {
            // 先设置全局变量，再触发加载
            currentGuildId = savedGuildId;
            currentGuildName = savedGuildName;
            currentChannelId = savedChannelId;

            // 更新UI块显示
            document.getElementById('server-name').textContent = savedGuildName;
            document.getElementById('server-info-container').style.display = 'block';
            document.getElementById('music-search-container').style.display = 'block';
            document.getElementById('player-container').style.display = 'block';
            document.getElementById('playlist-container').style.display = 'block';

            // 加载频道与播放列表
            loadChannels(savedGuildId);
            loadPlaylist(savedGuildId);
            if (socket) {
                socket.emit('join_room', { guild_id: savedGuildId });
            }
        }
    } catch (e) {
        console.warn('恢复上次选择失败:', e);
    }
}

// 初始化Socket.IO
function initializeSocketIO() {
    if (typeof io !== 'undefined') {
        socket = io();
        
        socket.on('connect', function() {
            console.log('Socket.IO连接成功');
        });
        
        socket.on('disconnect', function() {
            console.log('Socket.IO连接断开');
        });
        
        socket.on('playlist_update', function(data) {
            if (data.guild_id === currentGuildId) {
                updatePlaylist(data.playlist);
            }
        });
        
        socket.on('player_status', function(data) {
            if (data.guild_id === currentGuildId) {
                updatePlayerStatus(data);
            }
        });
    }
}

// 加载服务器列表
function loadGuilds() {
    console.log('开始加载服务器列表...');
    fetch('/api/guilds')
        .then(response => {
            console.log('服务器列表API响应状态:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('服务器列表API返回数据:', data);
            if (data.success) {
                displayGuilds(data.guilds);
            } else {
                showError('加载服务器列表失败: ' + data.error);
            }
        })
        .catch(error => {
            console.error('加载服务器列表异常:', error);
            showError('加载服务器列表异常: ' + error);
        });
}

// 显示服务器列表
function displayGuilds(guilds) {
    const guildList = document.getElementById('guild-list');
    
    if (!guilds || guilds.length === 0) {
        guildList.innerHTML = '<div class="text-center text-muted">没有可用的服务器</div>';
        return;
    }
    
    guildList.innerHTML = '';
    guilds.forEach(guild => {
        const guildItem = document.createElement('div');
        guildItem.className = 'guild-item';
        guildItem.dataset.id = guild.id;
        guildItem.innerHTML = `
            <div class="d-flex align-items-center">
                <img src="${guild.icon || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiByeD0iNCIgZmlsbD0iIzZDNzA3NyIvPgo8cGF0aCBkPSJNMTYgOEwxOCAxMkwxNiAxNkwxNCAxMkwxNiA4WiIgZmlsbD0id2hpdGUiLz4KPHBhdGggZD0iTTggMTZMMTIgMThMMTYgMTZMMTIgMTRMOSAxNloiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0xNiAyNEwxOCAyMEwxNiAxNkwxNCAyMEwxNiAyNFoiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0yNCAxNkwyMCAxOEwxNiAxNkwyMCAxNEwyNCAxNloiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo='}" 
                     class="rounded me-2" width="32" height="32" 
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiByeD0iNCIgZmlsbD0iIzZDNzA3NyIvPgo8cGF0aCBkPSJNMTYgOEwxOCAxMkwxNiAxNkwxNCAxMkwxNiA4WiIgZmlsbD0id2hpdGUiLz4KPHBhdGggZD0iTTggMTZMMTIgMThMMTYgMTZMMTIgMTRMOSAxNloiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0xNiAyNEwxOCAyMEwxNiAxNkwxNCAyMEwxNiAyNFoiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0yNCAxNkwyMCAxOEwxNiAxNkwyMCAxNEwyNCAxNloiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo='">
                <div>
                    <div class="fw-bold">${guild.name}</div>
                    <small class="text-muted">${guild.master_id ? '管理员' : '成员'}</small>
                </div>
            </div>
        `;
        
        guildItem.addEventListener('click', () => {
            selectGuild(guild.id, guild.name);
        });
        
        guildList.appendChild(guildItem);
    });

    // 自动选中并加载上次选择的服务器
    try {
        const savedGuildId = localStorage.getItem('currentGuildId');
        const savedGuildName = localStorage.getItem('currentGuildName');
        if (savedGuildId && savedGuildName) {
            // 如果当前未设置或不同，则自动触发选择
            if (currentGuildId !== savedGuildId) {
                selectGuild(savedGuildId, savedGuildName);
            } else {
                // 仅高亮
                document.querySelectorAll('#guild-list .guild-item').forEach(item => {
                    item.classList.toggle('active', item.dataset.id === savedGuildId);
                });
            }
        }
    } catch (e) {}
}

// 选择服务器
function selectGuild(guildId, guildName) {
    // 更新全局变量
    currentGuildId = guildId;
    currentGuildName = guildName;

    // 持久化选择
    try {
        localStorage.setItem('currentGuildId', guildId);
        localStorage.setItem('currentGuildName', guildName);
    } catch (e) {}
    
    // 更新UI
    document.querySelectorAll('#guild-list .guild-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.id === guildId) {
            item.classList.add('active');
        }
    });
    
    document.getElementById('server-name').textContent = guildName;
    document.getElementById('server-info-container').style.display = 'block';
    document.getElementById('music-search-container').style.display = 'block';
    document.getElementById('player-container').style.display = 'block';
    document.getElementById('playlist-container').style.display = 'block';
    
    // 加载频道列表
    loadChannels(guildId);
    
    // 加载播放列表
    loadPlaylist(guildId);
    
    // 如果Socket.IO可用，加入房间
    if (socket) {
        socket.emit('join_room', { guild_id: guildId });
    }
}

// 加载频道列表
function loadChannels(guildId) {
    fetch(`/api/channels?guild_id=${guildId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayChannels(data.channels);
            } else {
                showError('加载频道列表失败: ' + data.error);
            }
        })
        .catch(error => {
            showError('加载频道列表异常: ' + error);
        });
}

// 显示频道列表
function displayChannels(channels) {
    const channelSelect = document.getElementById('voice-channel-select');
    channelSelect.innerHTML = '<option value="">选择语音频道</option>';
    
    if (channels.length === 0) {
        channelSelect.innerHTML += '<option value="" disabled>没有可用的语音频道</option>';
        return;
    }
    
    channels.forEach(channel => {
        const option = document.createElement('option');
        option.value = channel.id;
        option.textContent = channel.name;
        channelSelect.appendChild(option);
    });
    
    // 启用加入按钮
    document.getElementById('join-btn').disabled = true;
    
    // 监听选择变化
    channelSelect.addEventListener('change', function() {
        currentChannelId = this.value;
        document.getElementById('join-btn').disabled = !currentChannelId;
        try {
            if (currentChannelId) {
                localStorage.setItem('currentChannelId', currentChannelId);
            } else {
                localStorage.removeItem('currentChannelId');
            }
        } catch (e) {}
    });

     // 恢复上次选择的频道
     try {
         const savedChannelId = localStorage.getItem('currentChannelId');
         if (savedChannelId) {
             channelSelect.value = savedChannelId;
             currentChannelId = savedChannelId;
             document.getElementById('join-btn').disabled = !currentChannelId;
         }
     } catch (e) {}
}



// 加载播放列表
function loadPlaylist(guildId) {
    fetch(`/api/playlist/current?guild_id=${guildId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updatePlaylist(data.playlist);
            } else {
                console.warn('加载播放列表失败: ' + data.error);
            }
        })
        .catch(error => {
            console.error('加载播放列表异常: ' + error);
        });
}

// 更新播放列表
function updatePlaylist(playlist) {
    const playlistBody = document.getElementById('playlist-body');
    playlistBody.innerHTML = '';
    
    if (!playlist || playlist.length === 0) {
        playlistBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">播放列表为空</td></tr>';
        return;
    }
    
    // 更新当前播放歌曲信息
    let nowPlaying = playlist.find(item => item.playing);
    if (nowPlaying) {
        document.getElementById('current-song').textContent = nowPlaying.name || '未知歌曲';
        document.getElementById('current-artist').textContent = nowPlaying.artist || '未知歌手';
        
        // 如果有进度信息，更新进度条
        if (nowPlaying.position !== undefined) {
            updateProgress(nowPlaying.position, nowPlaying.duration || 0);
        }
    } else {
        document.getElementById('current-song').textContent = '未播放';
        document.getElementById('current-artist').textContent = '-';
    }
    
    // 更新播放列表
    playlist.forEach((item, index) => {
        if (!item.playing) { // 只显示队列中的歌曲
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${item.name || '未知歌曲'}</td>
                <td>${item.artist || '未知歌手'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-danger remove-btn" data-index="${item.queue_index ?? index}">
                        <i class="bi bi-x"></i>
                    </button>
                </td>
            `;
            playlistBody.appendChild(row);
        }
    });
    
    // 绑定移除按钮事件
    document.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const index = this.dataset.index;
            removeFromPlaylist(index);
        });
    });
}

// 格式化时长
function formatDuration(seconds) {
    if (!seconds) return '--:--';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// 绑定事件处理函数
function bindEvents() {
    // 刷新按钮（如果存在）
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            if (currentGuildId) {
                loadPlaylist(currentGuildId);
            }
        });
    }
    
    // 加入频道按钮
    const joinBtn = document.getElementById('join-btn');
    if (joinBtn) {
        joinBtn.addEventListener('click', function() {
            if (currentGuildId && currentChannelId) {
                joinChannel(currentGuildId, currentChannelId);
            }
        });
    }
    
    // 离开频道按钮
    const leaveBtn = document.getElementById('leave-btn');
    if (leaveBtn) {
        leaveBtn.addEventListener('click', function() {
            if (currentGuildId) {
                leaveChannel(currentGuildId);
            }
        });
    }
    
    // 搜索按钮
    const searchBtn = document.getElementById('search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            const keyword = document.getElementById('search-input').value.trim();
            if (keyword) {
                searchMusic(keyword);
            }
        });
    }
    
    // 搜索输入框回车事件
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const keyword = this.value.trim();
                if (keyword) {
                    searchMusic(keyword);
                }
            }
        });
    }
    
    // 导入歌单按钮
    const playlistBtn = document.getElementById('playlist-btn');
    if (playlistBtn) {
        playlistBtn.addEventListener('click', function() {
            const playlistInput = document.getElementById('playlist-input').value.trim();
            if (playlistInput && currentGuildId) {
                importPlaylist(currentGuildId, playlistInput);
            }
        });
    }
    
    // 播放控制按钮
    const playBtn = document.getElementById('play-btn');
    if (playBtn) {
        playBtn.addEventListener('click', function() {
            if (currentGuildId) {
                resumeMusic(currentGuildId);
            }
        });
    }
    
    const pauseBtn = document.getElementById('pause-btn');
    if (pauseBtn) {
        pauseBtn.addEventListener('click', function() {
            if (currentGuildId) {
                pauseMusic(currentGuildId);
            }
        });
    }
    
    const skipBtn = document.getElementById('skip-btn');
    if (skipBtn) {
        skipBtn.addEventListener('click', function() {
            if (currentGuildId) {
                skipMusic(currentGuildId);
            }
        });
    }
    
    const stopBtn = document.getElementById('stop-btn');
    if (stopBtn) {
        stopBtn.addEventListener('click', function() {
            if (currentGuildId) {
                stopMusic(currentGuildId);
            }
        });
    }
    
    // 清空播放列表按钮
    const clearPlaylistBtn = document.getElementById('clear-playlist-btn');
    if (clearPlaylistBtn) {
        clearPlaylistBtn.addEventListener('click', function() {
            if (currentGuildId) {
                clearPlaylist(currentGuildId);
            }
        });
    }
}

// 显示错误信息
function showError(message) {
    console.error(message);
    // 使用Bootstrap的Toast或Alert组件显示错误
    alert('错误: ' + message);
}

// 显示成功信息
function showSuccess(message) {
    console.log(message);
    // 使用Bootstrap的Toast或Alert组件显示成功信息
    alert(message);
}

// 加入频道
function joinChannel(guildId, channelId) {
    fetch('/api/join', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            guild_id: guildId,
            channel_id: channelId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('leave-btn').disabled = false;
            showSuccess('成功加入语音频道');
            try { localStorage.setItem('currentChannelId', channelId); } catch (e) {}
        } else {
            showError('加入频道失败: ' + data.error);
        }
    })
    .catch(error => {
        showError('加入频道异常: ' + error);
    });
}

// 离开频道
function leaveChannel(guildId) {
    fetch('/api/leave', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            guild_id: guildId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('leave-btn').disabled = true;
            showSuccess('成功离开语音频道');
            try { localStorage.removeItem('currentChannelId'); } catch (e) {}
        } else {
            showError('离开频道失败: ' + data.error);
        }
    })
    .catch(error => {
        showError('离开频道异常: ' + error);
    });
}

// 搜索音乐
function searchMusic(keyword) {
    fetch(`/api/search?keyword=${encodeURIComponent(keyword)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displaySearchResults(data.songs);
            } else {
                showError('搜索音乐失败: ' + data.error);
            }
        })
        .catch(error => {
            showError('搜索音乐异常: ' + error);
        });
}

// 显示搜索结果
function displaySearchResults(songs) {
    const resultsBody = document.getElementById('search-results-body');
    resultsBody.innerHTML = '';
    
    if (!songs || songs.length === 0) {
        resultsBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">没有找到相关歌曲</td></tr>';
        document.getElementById('search-results').style.display = 'block';
        return;
    }
    
    songs.forEach(song => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${song.name}</td>
            <td>${song.ar ? song.ar.map(a => a.name).join(', ') : '-'}</td>
            <td>${song.al ? song.al.name : '-'}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary play-btn" data-id="${song.id}" data-name="${song.name}" data-artist="${song.ar ? song.ar[0].name : '-'}">
                    <i class="bi bi-play-fill"></i> 播放
                </button>
            </td>
        `;
        resultsBody.appendChild(row);
    });
    
    // 绑定播放按钮事件
    document.querySelectorAll('.play-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            console.log('播放按钮被点击:', {
                guildId: currentGuildId,
                songId: this.dataset.id,
                songName: this.dataset.name,
                artist: this.dataset.artist
            });
            
            if (currentGuildId) {
                playMusic(
                    currentGuildId,
                    this.dataset.id,
                    this.dataset.name,
                    this.dataset.artist
                );
            } else {
                showError('请先选择一个服务器');
            }
        });
    });
    
    document.getElementById('search-results').style.display = 'block';
}

// 播放音乐
function playMusic(guildId, songId, songName, artistName) {
    console.log('playMusic被调用:', {guildId, songId, songName, artistName, currentChannelId});
    
    if (!currentChannelId) {
        showError('请先选择一个语音频道');
        return;
    }
    
    const requestData = {
        guild_id: guildId,
        channel_id: currentChannelId,
        song_id: songId,
        song_name: songName,
        artist_name: artistName
    };
    
    console.log('发送播放请求:', requestData);
    
    fetch('/api/play', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        console.log('播放API响应状态:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('播放API响应数据:', data);
        if (data.success) {
            showSuccess(`已添加到播放列表: ${songName}`);
            // 刷新播放列表
            loadPlaylist(guildId);
        } else {
            showError('播放音乐失败: ' + data.error);
        }
    })
    .catch(error => {
        console.error('播放音乐异常:', error);
        showError('播放音乐异常: ' + error);
    });
}

// 导入歌单
function importPlaylist(guildId, playlistInput) {
    if (!currentChannelId) {
        showError('请先选择一个语音频道');
        return;
    }
    
    // 提取歌单ID
    let playlistId = playlistInput;
    
    // 如果是链接，提取ID
    if (playlistInput.includes('music.163.com')) {
        const match = playlistInput.match(/playlist\?id=(\d+)/);
        if (match) {
            playlistId = match[1];
        }
    }
    
    if (!playlistId || isNaN(playlistId)) {
        showError('请输入有效的歌单ID或链接');
        return;
    }
    
    fetch('/api/playlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            guild_id: guildId,
            channel_id: currentChannelId,
            playlist_id: playlistId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess(`已导入歌单，共${data.count}首歌曲`);
            // 刷新播放列表
            loadPlaylist(guildId);
        } else {
            showError('导入歌单失败: ' + data.error);
        }
    })
    .catch(error => {
        showError('导入歌单异常: ' + error);
    });
}

// 播放控制函数（已删除重复的空函数）

function pauseMusic(guildId) {
    fetch('/api/pause', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            guild_id: guildId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('已暂停播放');
        } else {
            showError('暂停失败: ' + data.error);
        }
    })
    .catch(error => {
        showError('暂停异常: ' + error);
    });
}

function resumeMusic(guildId) {
    fetch('/api/resume', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            guild_id: guildId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('已继续播放');
        } else {
            showError('继续播放失败: ' + data.error);
        }
    })
    .catch(error => {
        showError('继续播放异常: ' + error);
    });
}

function skipMusic(guildId) {
    fetch('/api/skip', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            guild_id: guildId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('已跳过当前歌曲');
            // 刷新播放列表
            loadPlaylist(guildId);
        } else {
            showError('跳过歌曲失败: ' + data.error);
        }
    })
    .catch(error => {
        showError('跳过歌曲异常: ' + error);
    });
}

function stopMusic(guildId) {
    fetch('/api/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            guild_id: guildId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('已停止播放');
            // 刷新播放列表
            loadPlaylist(guildId);
        } else {
            showError('停止失败: ' + data.error);
        }
    })
    .catch(error => {
        showError('停止异常: ' + error);
    });
}

// 更新进度条
function updateProgress(position, totalSeconds = 0) {
    const progressBar = document.getElementById('song-progress');
    const currentTime = document.getElementById('current-time');
    const totalTime = document.getElementById('total-time');
    
    // 格式化时间
    const minutes = Math.floor(position / 60);
    const seconds = Math.floor(position % 60);
    currentTime.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    if (totalSeconds && totalSeconds > 0) {
        const tMin = Math.floor(totalSeconds / 60);
        const tSec = Math.floor(totalSeconds % 60);
        totalTime.textContent = `${tMin.toString().padStart(2, '0')}:${tSec.toString().padStart(2, '0')}`;
    } else {
        totalTime.textContent = '00:00';
    }

    const denom = totalSeconds && totalSeconds > 0 ? totalSeconds : position > 0 ? position : 1;
    const percentage = Math.min(100, (position / denom) * 100);
    progressBar.style.width = `${percentage}%`;
}

// 清空播放列表
function clearPlaylist(guildId) {
    if (confirm('确定要清空播放列表吗？')) {
        fetch('/api/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                guild_id: guildId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess('播放列表已清空');
                loadPlaylist(guildId);
            } else {
                showError('清空失败: ' + data.error);
            }
        })
        .catch(error => {
            showError('清空异常: ' + error);
        });
    }
}

// 从播放列表中移除歌曲
function removeFromPlaylist(index) {
    if (confirm('确定要移除这首歌曲吗？')) {
        fetch('/api/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                guild_id: currentGuildId,
                index: index
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess('已移除歌曲');
                loadPlaylist(currentGuildId);
            } else {
                showError('移除失败: ' + data.error);
            }
        })
        .catch(error => {
            showError('移除异常: ' + error);
        });
    }
}

// 更新播放器状态
function updatePlayerStatus(data) {
    if (data.playing) {
        document.getElementById('current-song').textContent = data.song_name || '未知歌曲';
        document.getElementById('current-artist').textContent = data.artist_name || '未知歌手';
        updateProgress(data.position || 0);
    } else {
        document.getElementById('current-song').textContent = '未播放';
        document.getElementById('current-artist').textContent = '-';
        updateProgress(0);
    }
}