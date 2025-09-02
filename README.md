# 🎵 KOOK音乐机器人 Web控制台

[![DigitalOcean Referral Badge](https://web-platforms.sfo2.cdn.digitaloceanspaces.com/WWW/Badge%202.svg)](https://www.digitalocean.com/?refcode=8dcaa780cb2f&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge)

一个功能强大的KOOK音乐机器人Web控制台，支持网易云音乐播放、歌单管理、远程控制等功能。通过现代化的Web界面，让您轻松管理KOOK服务器的音乐播放。

## ✨ 项目优势

### 🎯 核心功能
- **🎵 音乐播放**: 支持网易云音乐搜索与播放，海量音乐资源
- **📋 歌单管理**: 一键导入网易云歌单，支持自定义播放列表
- **🌐 Web控制台**: 现代化响应式界面，支持多设备访问
- **🎮 远程控制**: 无需在KOOK中输入命令，通过Web界面即可控制
- **🔊 语音频道**: 自动加入用户所在语音频道，智能语音管理
- **⚡ 实时同步**: 支持多服务器同时管理，实时状态更新

### 🛠️ 技术特色
- **跨平台支持**: 同时支持Windows和Ubuntu系统
- **模块化设计**: 清晰的代码结构，易于维护和扩展
- **异步处理**: 基于asyncio的高性能异步架构
- **RESTful API**: 完整的API接口，支持第三方集成
- **实时通信**: 可选的Socket.IO支持，实现实时状态推送

## 🚀 快速开始

### 环境要求
- Python 3.8+
- FFmpeg (已内置Windows版本)
- KOOK机器人Token

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/VexMare/Kook_Web_Music.git
cd Kook_Web_Music
```

2. **选择系统版本**
```bash
# Windows用户
cd windows

# Ubuntu用户  
cd Ubuntu
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境**
```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件，填入您的KOOK机器人Token
# BOT_TOKEN=您的机器人Token
```

5. **启动应用**
```bash
python run.py
```

6. **访问控制台**
打开浏览器访问: `http://localhost:5000`

## 📖 使用指南

### 基础操作
1. **选择服务器**: 在左侧面板选择要管理的KOOK服务器
2. **加入语音频道**: 选择语音频道并点击"加入频道"
3. **搜索音乐**: 在搜索框输入歌曲名称或歌手
4. **播放控制**: 使用播放、暂停、跳过等控制按钮
5. **歌单导入**: 输入网易云歌单ID或链接，一键导入

### 高级功能
- **播放列表管理**: 查看、删除、清空播放列表
- **进度控制**: 拖拽进度条跳转到指定位置
- **多服务器支持**: 同时管理多个KOOK服务器
- **实时状态**: 查看当前播放状态和队列信息

## 🎛️ 机器人命令

除了Web控制台，机器人还支持以下KOOK命令：

| 命令 | 功能 | 示例 |
|------|------|------|
| `/ping` | 测试机器人连接 | `/ping` |
| `/加入` | 加入用户所在语音频道 | `/加入` |
| `/wy 歌曲名` | 播放网易云音乐 | `/wy 稻香` |
| `/wygd 歌单ID` | 播放网易云歌单 | `/wygd 123456789` |
| `/暂停` | 暂停播放 | `/暂停` |
| `/继续` | 继续播放 | `/继续` |
| `/跳过` | 跳过当前歌曲 | `/跳过` |
| `/停止` | 停止播放 | `/停止` |

## 🏗️ 项目结构

```
Kook_Web_Music/
├── windows/                 # Windows版本
│   ├── app.py              # 主应用文件
│   ├── routes.py           # 路由定义
│   ├── config.py           # 配置文件
│   ├── kookvoice/          # 语音处理模块
│   ├── templates/          # HTML模板
│   ├── static/             # 静态资源
│   └── ffmpeg/             # FFmpeg工具
├── Ubuntu/                 # Ubuntu版本
└── README.md              # 项目说明
```

## 🔧 配置说明

### 环境变量
```bash
# KOOK机器人Token (必需)
BOT_TOKEN=您的机器人Token

# FFmpeg路径 (可选，已内置)
FFMPEG_PATH=./ffmpeg/bin/ffmpeg.exe

# 音乐API地址 (可选)
MUSIC_API_BASE=https://api.example.com

# Web应用密钥 (可选)
SECRET_KEY=your_secret_key
```

### 机器人权限
确保您的KOOK机器人具有以下权限：
- 发送消息
- 管理频道
- 连接语音频道
- 发送语音消息

## 🌐 部署到云端

### 使用DigitalOcean部署

我们推荐使用[DigitalOcean](https://m.do.co/c/8dcaa780cb2f)来部署您的音乐机器人，享受以下优势：

- **💰 免费额度**: 新用户注册即可获得$200信用额度
- **⚡ 高性能**: SSD存储，全球数据中心
- **🔒 安全可靠**: 99.99% SLA保证
- **📈 弹性扩展**: 按需升级配置
- **🛠️ 简单易用**: 一键部署，图形化管理

#### 部署步骤：

1. **注册DigitalOcean账户**
   - 访问: https://m.do.co/c/8dcaa780cb2f
   - 注册新账户，获得$200免费额度

2. **创建Droplet**
   - 选择Ubuntu 20.04 LTS
   - 推荐配置: 1GB RAM, 1 CPU, 25GB SSD
   - 选择合适的数据中心位置

3. **配置服务器**
   ```bash
   # 更新系统
   sudo apt update && sudo apt upgrade -y
   
   # 安装Python和依赖
   sudo apt install python3 python3-pip git -y
   
   # 克隆项目
   git clone https://github.com/VexMare/Kook_Web_Music.git
   cd Kook_Web_Music/Ubuntu
   
   # 安装依赖
   pip3 install -r requirements.txt
   
   # 配置环境变量
   nano .env
   
   # 启动应用
   python3 run.py
   ```

4. **设置反向代理** (可选)
   ```bash
   # 安装Nginx
   sudo apt install nginx -y
   
   # 配置反向代理
   sudo nano /etc/nginx/sites-available/kook-music
   ```

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献
1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

### 报告问题
如果您发现了bug或有功能建议，请：
1. 检查现有的Issues
2. 创建新的Issue，详细描述问题
3. 提供复现步骤和环境信息

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [KOOK官方API](https://developer.kookapp.cn/) - 提供机器人开发支持
- [网易云音乐API](https://github.com/Binaryify/NeteaseCloudMusicApi) - 音乐资源支持
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Bootstrap](https://getbootstrap.com/) - UI框架
- [DigitalOcean](https://www.digitalocean.com/?refcode=8dcaa780cb2f) - 云服务器支持

## 📞 支持与联系

- **GitHub Issues**: [提交问题](https://github.com/VexMare/Kook_Web_Music/issues)
- **文档**: 查看项目Wiki获取详细文档
- **社区**: 加入我们的讨论群组

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**

[![DigitalOcean Referral Badge](https://web-platforms.sfo2.cdn.digitaloceanspaces.com/WWW/Badge%202.svg)](https://www.digitalocean.com/?refcode=8dcaa780cb2f&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge)

**使用我们的推荐链接注册DigitalOcean，获得$200免费额度！**

</div>
