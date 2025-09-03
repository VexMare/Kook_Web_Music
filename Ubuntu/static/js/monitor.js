// 监控页面JavaScript
class SystemMonitor {
    constructor() {
        this.resourceChart = null;
        this.networkChart = null;
        this.updateInterval = null;
        this.terminalUpdateInterval = null;
        this.isTerminalConnected = false;
        this.autoScroll = true;
        this.terminalLineCount = 0;
        this.maxTerminalLines = 1000;
        this.lastFilePosition = 0; // 记录上次读取的文件位置
        this.resourceData = {
            cpu: [],
            memory: [],
            labels: []
        };
        this.networkData = {
            sent: [],
            received: [],
            labels: []
        };
        this.maxDataPoints = 20;
        
        this.init();
    }

    init() {
        this.initCharts();
        this.bindEvents();
        this.startMonitoring();
    }

    initCharts() {
        // 系统资源图表
        const resourceCtx = document.getElementById('resourceChart').getContext('2d');
        this.resourceChart = new Chart(resourceCtx, {
            type: 'line',
            data: {
                labels: this.resourceData.labels,
                datasets: [{
                    label: 'CPU使用率 (%)',
                    data: this.resourceData.cpu,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }, {
                    label: '内存使用率 (%)',
                    data: this.resourceData.memory,
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                    }
                }
            }
        });

        // 网络流量图表
        const networkCtx = document.getElementById('networkChart').getContext('2d');
        this.networkChart = new Chart(networkCtx, {
            type: 'line',
            data: {
                labels: this.networkData.labels,
                datasets: [{
                    label: '发送 (MB)',
                    data: this.networkData.sent,
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    tension: 0.1
                }, {
                    label: '接收 (MB)',
                    data: this.networkData.received,
                    borderColor: 'rgb(255, 205, 86)',
                    backgroundColor: 'rgba(255, 205, 86, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                    }
                }
            }
        });
    }

    bindEvents() {
        // 终端连接按钮 - 只用于连接，不提供断开功能
        $('#connect-terminal-btn').click(() => {
            if (!this.isTerminalConnected) {
                this.connectTerminal();
            }
        });

        // 终端自动滚动按钮
        $('#auto-scroll-terminal-btn').click(() => {
            this.toggleTerminalAutoScroll();
        });



        // 手动清理按钮
        $('#manual-cleanup-btn').click(() => {
            this.manualCleanup();
        });

        // 更新清理阈值按钮
        $('#update-threshold-btn').click(() => {
            this.updateCleanupThreshold();
        });

        // 测试缓存按钮
        $('#test-cache-btn').click(() => {
            this.testCache();
        });

        // 终端滚动事件
        $('#terminal-container').scroll(() => {
            this.handleTerminalScroll();
        });
    }

    async startMonitoring() {
        // 立即更新一次
        await this.updateSystemStatus();
        
        // 设置定时更新
        this.updateInterval = setInterval(() => {
            this.updateSystemStatus();
        }, 5000); // 每5秒更新一次

        // 自动连接终端输出
        this.connectTerminal();
    }

    async updateSystemStatus() {
        try {
            const response = await fetch('/api/system/status');
            const data = await response.json();
            
            if (data.success) {
                this.updateMetrics(data);
                this.updateCharts(data);
                this.updateStatus(data);
            } else {
                console.error('获取系统状态失败:', data.error);
            }
        } catch (error) {
            console.error('更新系统状态异常:', error);
        }
    }

    updateMetrics(data) {
        // 更新概览指标
        $('#cpu-usage').text(data.system.cpu_percent.toFixed(1) + '%');
        $('#memory-usage').text(data.system.memory.percent.toFixed(1) + '%');
        $('#disk-usage').text(data.system.disk.percent.toFixed(1) + '%');
        
        // 更新进程运行时间
        const uptime = data.process.uptime;
        const hours = Math.floor(uptime / 3600);
        const minutes = Math.floor((uptime % 3600) / 60);
        $('#process-uptime').text(`${hours}h ${minutes}m`);

        // 更新播放统计
        $('#active-guilds').text(data.playback.active_guilds);
        $('#playing-songs').text(data.playback.playing_songs);
        $('#queued-songs').text(data.playback.queued_songs);

        // 更新音频缓存信息
        $('#cache-count').text(data.audio_cache.count);
        $('#cache-max').text(data.audio_cache.max_size);
        $('#cache-size').text(data.audio_cache.size_mb.toFixed(2) + ' MB');
        
        const cachePercent = (data.audio_cache.count / data.audio_cache.max_size) * 100;
        $('#cache-progress').css('width', cachePercent + '%');

        // 更新清理统计信息
        if (data.cleanup_stats) {
            $('#cleanup-threshold').text(data.cleanup_stats.cleanup_threshold);
            $('#threshold-input').val(data.cleanup_stats.cleanup_threshold);
            
            // 显示播放计数
            const playCounts = data.cleanup_stats.song_play_count;
            if (Object.keys(playCounts).length > 0) {
                const countText = Object.entries(playCounts)
                    .map(([guild, count]) => `服务器${guild.substring(0, 8)}: ${count}首`)
                    .join(', ');
                $('#play-counts').text(countText);
            } else {
                $('#play-counts').text('无');
            }
        }
    }

    updateCharts(data) {
        const now = new Date().toLocaleTimeString();
        
        // 更新资源图表数据
        this.resourceData.labels.push(now);
        this.resourceData.cpu.push(data.system.cpu_percent);
        this.resourceData.memory.push(data.system.memory.percent);
        
        // 更新网络图表数据
        this.networkData.labels.push(now);
        this.networkData.sent.push((data.system.network.bytes_sent / 1024 / 1024).toFixed(2));
        this.networkData.received.push((data.system.network.bytes_recv / 1024 / 1024).toFixed(2));
        
        // 限制数据点数量
        if (this.resourceData.labels.length > this.maxDataPoints) {
            this.resourceData.labels.shift();
            this.resourceData.cpu.shift();
            this.resourceData.memory.shift();
            this.networkData.labels.shift();
            this.networkData.sent.shift();
            this.networkData.received.shift();
        }
        
        // 更新图表
        this.resourceChart.update();
        this.networkChart.update();
    }

    updateStatus(data) {
        // 更新系统状态指示器
        const cpuStatus = data.system.cpu_percent > 80 ? 'warning' : 'ok';
        const memoryStatus = data.system.memory.percent > 80 ? 'warning' : 'ok';
        const diskStatus = data.system.disk.percent > 90 ? 'error' : 'ok';
        
        $('#system-status').html(`
            <span class="status-indicator status-${cpuStatus}"></span>
            CPU: ${data.system.cpu_percent.toFixed(1)}% | 
            <span class="status-indicator status-${memoryStatus}"></span>
            内存: ${data.system.memory.percent.toFixed(1)}%
        `);
        
        // 更新进程状态
        const processStatus = data.process.cpu_percent > 50 ? 'warning' : 'ok';
        $('#process-status').html(`
            <span class="status-indicator status-${processStatus}"></span>
            PID: ${data.process.pid} | CPU: ${data.process.cpu_percent.toFixed(1)}%
        `);
        
        // 更新缓存状态
        const cacheStatus = data.audio_cache.count >= data.audio_cache.max_size ? 'warning' : 'ok';
        $('#cache-status').text(`正常 (${data.audio_cache.count}/${data.audio_cache.max_size})`);
        
        // 更新播放状态
        const playbackStatus = data.playback.active_guilds > 0 ? 'ok' : 'warning';
        $('#playback-status').text(`正常 (${data.playback.active_guilds}个服务器)`);
    }

    async connectTerminal() {
        if (this.isTerminalConnected) return;
        
        this.updateTerminalStatus('connecting');
        
        try {
            // 重置文件位置，从头开始读取
            this.lastFilePosition = 0;
            
            // 开始定时获取终端输出
            this.terminalUpdateInterval = setInterval(() => {
                this.fetchTerminalOutput();
            }, 1000); // 每秒更新一次
            
            this.isTerminalConnected = true;
            this.updateTerminalStatus('connected');
            this.addTerminalLineDirect('已连接到终端输出流...');
            
        } catch (error) {
            console.error('连接失败:', error);
            this.addTerminalLine('系统', 'error', `连接失败: ${error.message}`);
            this.updateTerminalStatus('disconnected');
        }
    }



    async fetchTerminalOutput() {
        try {
            const response = await fetch(`/api/terminal/output?last_position=${this.lastFilePosition}`);
            const data = await response.json();
            
            if (data.success) {
                // 调试信息
                console.log(`终端输出 - 文件大小: ${data.file_size}, 上次位置: ${this.lastFilePosition}, 新内容长度: ${data.output ? data.output.length : 0}`);
                
                // 更新文件位置
                this.lastFilePosition = data.file_size;
                
                // 处理新的输出 - 直接显示，不做过滤
                if (data.output) {
                    const lines = data.output.split('\n');
                    lines.forEach(line => {
                        // 移除行尾的换行符和空白字符
                        const cleanLine = line.replace(/\r?\n$/, '').trimEnd();
                        if (cleanLine !== '') {
                            this.addTerminalLineDirect(cleanLine);
                        }
                    });
                }
            }
        } catch (error) {
            console.error('获取终端输出失败:', error);
            if (this.isTerminalConnected) {
                this.addTerminalLineDirect(`获取输出失败: ${error.message}`);
            }
        }
    }

    parseAndAddTerminalLine(line) {
        // 跳过空行和无效行
        const trimmedLine = line.trim();
        if (!trimmedLine || 
            trimmedLine.length < 3 || 
            trimmedLine.match(/^[\s\-=*]+$/) ||
            trimmedLine === 'nohup: ignoring input') {
            return;
        }
        
        // 解析日志行格式
        const timestampMatch = line.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})/);
        const levelMatch = line.match(/- (INFO|ERROR|WARNING|DEBUG) -/);
        
        let timestamp = '';
        let level = 'info';
        let message = line;
        
        if (timestampMatch) {
            timestamp = timestampMatch[1];
            message = line.substring(timestamp.length + 1);
        }
        
        if (levelMatch) {
            level = levelMatch[1].toLowerCase();
            message = message.replace(/- (INFO|ERROR|WARNING|DEBUG) -/, '').trim();
        }
        
        // 清理消息内容，移除多余的空格
        message = message.trim();
        
        // 过滤掉一些常见的无用信息
        const filteredPatterns = [
            '*', 'WARNING:', 'Use a production', 'Environment:', 'Debug mode:', 
            'Serving Flask', 'This is a development', 'Use a production WSGI',
            'nohup:', 'ignoring input'
        ];
        
        const shouldFilter = filteredPatterns.some(pattern => 
            message.startsWith(pattern) || message.includes(pattern)
        );
        
        if (message && !shouldFilter && message.length > 2) {
            this.addTerminalLine(timestamp || '终端', level, message);
        }
    }

    addTerminalLineDirect(line) {
        const output = $('#terminal-output');
        const lineNumber = ++this.terminalLineCount;
        
        // 清理行内容，移除多余的空白字符
        const cleanLine = line.trim();
        
        // 直接显示清理后的行内容，去掉terminal-line包装
        const lineElement = $(`
            <span class="line-number">${lineNumber.toString().padStart(4, '0')}</span>
            <span class="terminal-output-text">${this.escapeHtml(cleanLine)}</span>
        `);
        
        output.append(lineElement);
        
        // 限制最大行数
        if (this.terminalLineCount > this.maxTerminalLines) {
            output.find('.line-number').first().next('.terminal-output-text').andSelf().remove();
        }
        
        // 自动滚动
        if (this.autoScroll) {
            this.scrollTerminalToBottom();
        }
    }

    addTerminalLine(source, level, message) {
        const output = $('#terminal-output');
        const lineNumber = ++this.terminalLineCount;
        
        const lineClass = `terminal-${level}`;
        const timestamp = new Date().toLocaleTimeString();
        
        // 简化显示格式，减少不必要的元素和空格
        const lineElement = $(`
            <div class="terminal-line">
                <span class="line-number">${lineNumber.toString().padStart(4, '0')}</span>
                <span class="timestamp">[${timestamp}]</span>
                <span class="${lineClass}">${this.escapeHtml(message)}</span>
            </div>
        `);
        
        output.append(lineElement);
        
        // 限制最大行数
        if (this.terminalLineCount > this.maxTerminalLines) {
            output.find('.terminal-line').first().remove();
        }
        
        // 自动滚动
        if (this.autoScroll) {
            this.scrollTerminalToBottom();
        }
    }



    toggleTerminalAutoScroll() {
        this.autoScroll = !this.autoScroll;
        const btn = $('#auto-scroll-terminal-btn');
        
        if (this.autoScroll) {
            btn.html('<i class="bi bi-arrow-down-circle-fill"></i> 自动滚动');
            btn.removeClass('btn-outline-warning').addClass('btn-warning');
            this.scrollTerminalToBottom();
        } else {
            btn.html('<i class="bi bi-arrow-down-circle"></i> 自动滚动');
            btn.removeClass('btn-warning').addClass('btn-outline-warning');
        }
    }

    scrollTerminalToBottom() {
        const container = $('#terminal-container');
        container.scrollTop(container[0].scrollHeight);
    }

    handleTerminalScroll() {
        const container = $('#terminal-container');
        const isAtBottom = container.scrollTop() + container.height() >= container[0].scrollHeight - 10;
        
        if (isAtBottom && !this.autoScroll) {
            this.autoScroll = true;
            $('#auto-scroll-terminal-btn').html('<i class="bi bi-arrow-down-circle-fill"></i> 自动滚动');
        }
    }

    updateTerminalStatus(status = 'disconnected') {
        const statusElement = $('#terminal-status-badge');
        const connectBtn = $('#connect-terminal-btn');
        
        switch (status) {
            case 'connected':
                statusElement.removeClass('bg-warning bg-danger').addClass('bg-success');
                statusElement.html('<i class="bi bi-check-circle"></i> 实时更新');
                connectBtn.html('<i class="bi bi-check-circle"></i> 已连接');
                connectBtn.removeClass('btn-outline-success btn-danger').addClass('btn-success');
                connectBtn.prop('disabled', true);
                break;
            case 'connecting':
                statusElement.removeClass('bg-success bg-danger').addClass('bg-warning');
                statusElement.html('<i class="bi bi-arrow-clockwise spinning"></i> 连接中...');
                connectBtn.html('<i class="bi bi-hourglass-split"></i> 连接中');
                connectBtn.prop('disabled', true);
                break;
            case 'disconnected':
            default:
                statusElement.removeClass('bg-success bg-warning').addClass('bg-danger');
                statusElement.html('<i class="bi bi-exclamation-triangle"></i> 未连接');
                connectBtn.html('<i class="bi bi-play-circle"></i> 连接');
                connectBtn.removeClass('btn-danger').addClass('btn-outline-success');
                connectBtn.prop('disabled', false);
                break;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async manualCleanup() {
        if (!confirm('确定要手动清理缓存和内存吗？这将完全清空所有音频缓存并重置播放计数。')) {
            return;
        }

        try {
            const response = await fetch('/api/system/cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            if (data.success) {
                alert(`清理完成！\n清理前: ${data.details.cache_before} 个缓存项\n清理后: ${data.details.cache_after} 个缓存项\n实际清理: ${data.details.cache_cleared} 个缓存项\n释放了 ${data.details.memory_freed_mb} MB 内存`);
                // 立即更新系统状态
                await this.updateSystemStatus();
            } else {
                alert('清理失败: ' + data.error);
            }
        } catch (error) {
            console.error('手动清理异常:', error);
            alert('手动清理异常: ' + error.message);
        }
    }

    async updateCleanupThreshold() {
        const newThreshold = parseInt($('#threshold-input').val());
        
        if (isNaN(newThreshold) || newThreshold < 1 || newThreshold > 10) {
            alert('清理阈值必须在1-10之间');
            return;
        }

        try {
            const response = await fetch('/api/system/cleanup/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ threshold: newThreshold })
            });

            const data = await response.json();
            if (data.success) {
                alert(data.message);
                // 立即更新系统状态
                await this.updateSystemStatus();
            } else {
                alert('更新失败: ' + data.error);
            }
        } catch (error) {
            console.error('更新清理阈值异常:', error);
            alert('更新清理阈值异常: ' + error.message);
        }
    }

    async testCache() {
        try {
            const response = await fetch('/api/cache/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            if (data.success) {
                alert(`测试缓存成功！\n${data.message}\n当前缓存数量: ${data.cache_count}`);
                // 立即更新系统状态
                await this.updateSystemStatus();
            } else {
                alert('测试缓存失败: ' + data.error);
            }
        } catch (error) {
            console.error('测试缓存异常:', error);
            alert('测试缓存异常: ' + error.message);
        }
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        if (this.terminalUpdateInterval) {
            clearInterval(this.terminalUpdateInterval);
        }
    }
}

// 页面加载完成后初始化监控
$(document).ready(() => {
    window.systemMonitor = new SystemMonitor();
});

// 页面卸载时清理资源
$(window).on('beforeunload', () => {
    if (window.systemMonitor) {
        window.systemMonitor.destroy();
    }
});
