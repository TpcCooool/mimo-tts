# MiMo TTS

> 基于小米 MiMo TTS V2.5 API 的在线语音合成工具

[English](./README_EN.md) | 中文

一款轻量级的 Web 端文本转语音应用，使用小米 MiMo TTS V2.5 API，支持中英文语音合成、声音设计和声音克隆。采用 Neo-Brutalism 设计风格，界面简洁有个性。

## 功能特性

- **语音合成** — 支持中文和英文文本转语音
- **内置音色** — 9 种预设音色：冰糖、茉莉、苏打、白桦、Mia、Chloe、Milo、Dean 等
- **声音设计** — 用自然语言描述想要的声音，AI 自动生成（如"温柔的年轻女声，语速缓慢，轻声细语"）
- **声音克隆** — 上传音频或视频样本，克隆声音进行合成
- **导演模式** — 通过自然语言指令控制说话风格（如"用激动的电视主持人风格朗读"）
- **音频标签** — 在文本中插入 `(叹气)`、`(笑)`、`(唱歌)` 等标签，实现富有表现力的语音效果
- **格式下载** — 支持 WAV 和 MP3 格式下载

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Vue 3 (Composition API) |
| 构建工具 | Vite 8 |
| 样式 | Vanilla CSS (Neo-Brutalism) |
| 音频处理 | lamejs (WAV → MP3) |
| 部署平台 | Vercel |

## 快速开始

### 前置条件

- Node.js 18+
- MiMo API Key（前往 [MiMo 平台](https://platform.xiaomimimo.com/#/console/api-keys) 获取）

### 安装与运行

```bash
# 克隆项目
git clone https://github.com/your-username/mimo-tts.git
cd mimo-tts

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key

# 本地开发
npm run dev
```

### 环境变量

在 `.env` 文件中配置：

```env
MIMO_API_KEY=your_api_key_here
MIMO_API_BASE_URL=https://api.xiaomimimo.com/v1
```

### 部署到 Vercel

```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署
vercel
```

在 Vercel 项目设置中添加环境变量 `MIMO_API_KEY`。

## 项目结构

```
mimo-tts/
├── api/                  # Vercel Serverless Functions
│   ├── tts.js            # TTS 接口代理
│   └── health.js         # 健康检查
├── src/
│   ├── App.vue           # 主应用组件
│   ├── main.js           # 入口文件
│   └── style.css         # 全局样式
├── public/               # 静态资源
├── index.html            # HTML 入口
├── vite.config.js        # Vite 配置
└── vercel.json           # Vercel 部署配置
```


## License

[MIT License](./LICENSE)
