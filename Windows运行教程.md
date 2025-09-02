# KOOK音乐机器人Web控制台

这是一个基于Flask的KOOK音乐机器人Web控制台，可以通过Web界面控制KOOK音乐机器人的播放功能。

## 功能特点

- 服务器管理：查看和选择服务器
- 频道管理：加入/离开语音频道
- 音乐搜索：搜索网易云音乐
- 歌单导入：导入网易云歌单
- 播放控制：播放、暂停、跳过、调整进度
- 播放列表管理：查看、添加、删除歌曲

## 安装

安装依赖
```bash
pip install -r requirements.txt
```

配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填写必要的配置信息
```

运行应用
```bash
python run.py
```

## 配置

在`.env`文件中配置以下参数：

- `BOT_TOKEN`：KOOK机器人的Token
- `FFMPEG_PATH`：FFmpeg可执行文件的路径
- `MUSIC_API_BASE`：音乐API的基础URL
- `SECRET_KEY`：Web应用的密钥

## 技术栈

- 后端：Flask, Python
- 前端：Bootstrap 5, JavaScript
- 音频处理：FFmpeg
- 实时通信：Socket.IO (可选)

## 许可证

MIT