# KOOK音乐机器人Web控制台 - Ubuntu系统运行教程

## 项目简介

这是一个基于Flask的KOOK音乐机器人Web控制台，可以通过Web界面控制KOOK音乐机器人的播放功能。

### 主要功能
- 服务器管理：查看和选择服务器
- 频道管理：加入/离开语音频道
- 音乐搜索：搜索网易云音乐
- 歌单导入：导入网易云歌单
- 播放控制：播放、暂停、跳过、调整进度
- 播放列表管理：查看、添加、删除歌曲

## 系统要求

### 硬件要求
- CPU: 1核心以上
- 内存: 512MB以上
- 硬盘: 1GB可用空间

### 软件要求
- Ubuntu 18.04 LTS 或更高版本
- Python 3.7 或更高版本
- FFmpeg (用于音频处理)

## 安装步骤

### 1. 更新系统包

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. 安装Python和pip

```bash
# 安装Python3和pip
sudo apt install python3 python3-pip python3-venv -y

# 验证安装
python3 --version
pip3 --version
```

### 3. 安装FFmpeg

```bash
# 安装FFmpeg
sudo apt install ffmpeg -y

# 验证安装
ffmpeg -version
```

### 4. 安装Git（如果未安装）

```bash
sudo apt install git -y
```

### 5. 克隆或下载项目

如果您有Git仓库：
```bash
git clone <项目仓库地址>
cd Main
```

或者直接下载项目文件到 `/www/wwwroot/Main` 目录。

### 6. 创建Python虚拟环境

```bash
# 进入项目目录
cd /www/wwwroot/Main

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 7. 安装Python依赖

```bash
# 确保在虚拟环境中
pip install --upgrade pip
pip install -r requirements.txt
```

### 8. 配置环境变量

#### 方法一：使用提供的脚本创建.env文件

```bash
python3 create_env.py
```

#### 方法二：手动创建.env文件

```bash
nano .env
```

在文件中添加以下内容：

```env
# KOOK机器人配置
BOT_TOKEN=你的KOOK机器人Token

# FFMPEG配置 (Ubuntu系统路径)
FFMPEG_PATH=/usr/bin/ffmpeg
FFPROBE_PATH=/usr/bin/ffprobe

# 音乐API配置
MUSIC_API_BASE=https://1304404172-f3na0r58ws.ap-beijing.tencentscf.com

# Web控制台配置
SECRET_KEY=kook_web_music_secret_key
HOST=0.0.0.0
PORT=5000
DEBUG=True
```

**重要提示：**
- 将 `BOT_TOKEN` 替换为您的实际KOOK机器人Token
- FFMPEG路径在Ubuntu系统中通常是 `/usr/bin/ffmpeg`

### 9. 设置文件权限

```bash
# 确保运行脚本有执行权限
chmod +x run.py
chmod +x create_env.py
```

### 10. 运行项目

#### 开发模式运行

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 运行项目
python3 run.py
```

#### 后台运行

```bash
# 使用nohup后台运行
nohup python3 run.py > app.log 2>&1 &

# 查看进程
ps aux | grep python3

# 查看日志
tail -f app.log
```

#### 使用systemd服务（推荐生产环境）

创建服务文件：
```bash
sudo nano /etc/systemd/system/kook-music-bot.service
```

添加以下内容：
```ini
[Unit]
Description=KOOK Music Bot Web Console
After=network.target

[Service]
Type=simple
User=你的用户名
WorkingDirectory=/www/wwwroot/Main
Environment=PATH=/www/wwwroot/Main/venv/bin
ExecStart=/www/wwwroot/Main/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用并启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable kook-music-bot
sudo systemctl start kook-music-bot
sudo systemctl status kook-music-bot
```

### 11. 访问Web控制台

项目启动后，在浏览器中访问：
```
http://你的服务器IP:5000
```

例如：`http://192.168.1.100:5000`

## 配置说明

### 环境变量详解

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| BOT_TOKEN | KOOK机器人的Token | 需要配置 |
| FFMPEG_PATH | FFmpeg可执行文件路径 | /usr/bin/ffmpeg |
| FFPROBE_PATH | FFprobe可执行文件路径 | /usr/bin/ffprobe |
| MUSIC_API_BASE | 音乐API基础URL | 已配置 |
| SECRET_KEY | Web应用密钥 | 可自定义 |
| HOST | 服务器监听地址 | 0.0.0.0 |
| PORT | 服务器端口 | 5000 |
| DEBUG | 调试模式 | True |

### 防火墙配置

如果使用防火墙，需要开放5000端口：

```bash
# UFW防火墙
sudo ufw allow 5000

# 或者iptables
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

## 常见问题解决

### 1. Python版本问题

如果遇到Python版本过低：
```bash
# 安装Python 3.8+
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-pip
```

### 2. FFmpeg未找到

```bash
# 重新安装FFmpeg
sudo apt remove ffmpeg
sudo apt update
sudo apt install ffmpeg

# 验证安装
which ffmpeg
ffmpeg -version
```

### 3. 端口被占用

```bash
# 查看端口占用
sudo netstat -tlnp | grep :5000

# 杀死占用进程
sudo kill -9 进程ID

# 或者修改.env文件中的PORT配置
```

### 4. 权限问题

```bash
# 确保项目目录权限正确
sudo chown -R $USER:$USER /www/wwwroot/Main
chmod -R 755 /www/wwwroot/Main
```

### 5. 依赖安装失败

```bash
# 更新pip
pip install --upgrade pip

# 清理缓存重新安装
pip install -r requirements.txt --no-cache-dir
```

### 6. 虚拟环境问题

```bash
# 删除并重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 日志查看

### 应用日志
```bash
# 查看实时日志
tail -f app.log

# 查看错误日志
tail -f debug.log
```

### 系统服务日志
```bash
# 查看systemd服务日志
sudo journalctl -u kook-music-bot -f
```

## 性能优化

### 1. 生产环境配置

修改 `.env` 文件：
```env
DEBUG=False
HOST=127.0.0.1  # 如果使用反向代理
```

### 2. 使用Nginx反向代理

安装Nginx：
```bash
sudo apt install nginx -y
```

创建配置文件：
```bash
sudo nano /etc/nginx/sites-available/kook-music-bot
```

添加配置：
```nginx
server {
    listen 80;
    server_name 你的域名或IP;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/kook-music-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 维护和更新

### 更新项目
```bash
# 停止服务
sudo systemctl stop kook-music-bot

# 备份当前版本
cp -r /www/wwwroot/Main /www/wwwroot/Main.backup

# 更新代码（如果有Git仓库）
git pull

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
sudo systemctl start kook-music-bot
```

### 定期维护
```bash
# 清理日志文件
find /www/wwwroot/Main -name "*.log" -mtime +7 -delete

# 更新系统包
sudo apt update && sudo apt upgrade -y
```

## 技术支持

如果遇到问题，请检查：
1. 系统日志：`sudo journalctl -u kook-music-bot`
2. 应用日志：`tail -f app.log`
3. 网络连接：`curl http://localhost:5000`
4. 进程状态：`ps aux | grep python3`

---

**注意：** 本教程基于Ubuntu系统编写，其他Linux发行版可能需要调整部分命令。请根据您的具体环境进行相应调整。
