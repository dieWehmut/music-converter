<h1 style="text-align: center;">Music Converter</h1>

<div align="center">

简体中文 | [繁體中文](docs/README.zh-TW.md) | [English](docs/README.en.md) | [日本語](docs/README.ja.md)

</div>

---

# 目录

<details>
<summary>展开/收起</summary>

- [目录](#目录)
- [项目简介](#项目简介)
- [项目背景](#项目背景)
- [功能亮点](#功能亮点)
- [技术实现](#技术实现)
  - [主要内容](#主要内容)
  - [目录概览](#目录概览)
  - [环境要求](#环境要求)
  - [本地测试](#本地测试)
    - [后端设置](#后端设置)
    - [前端设置](#前端设置)
    - [API测试](#api测试)
  - [部署说明](#部署说明)
    - [后端部署](#后端部署)
    - [前端部署](#前端部署)
  - [API 说明](#api-说明)
    - [异步任务](#异步任务)
    - [响应字段](#响应字段)
    - [环境变量](#环境变量)
  - [故障排查](#故障排查)
- [价值与展望](#价值与展望)
- [第三方说明](#第三方说明)
  - [核心模型](#核心模型)
  - [基础框架](#基础框架)
- [写在最后](#写在最后)

</details>

# 项目简介

Music Converter 是一套端到端的音乐情绪/风格转换实验项目。用户上传受支持的音频（WAV、MP3 等），系统先解析其风格与情绪特征，再依据目标风格与情绪生成新的编曲。前端由 Vue 3 + Vite 驱动，后端使用 FastAPI，对接深度学习推理管线。

# 项目背景
随着数字音乐产业的蓬勃发展，用户对音乐个性化改编的需求日益增长。传统音乐风格往往往往依赖专业音乐人手动创作，成本高、周期长，难以满足普通用户快速变化的多样化需求。尤其在风格迁移与情绪转换场景中，需要同时兼顾原曲旋律特征与目标风格的融合，传统人工制作方式难以高效实现批量处理。

本项目旨在通过深度学习技术，构建一套自动化的音乐情绪与风格转换系统，核心解决核心解决三大痛点：

- **1.技术门槛高**：借助 YAMNet 模型的音频特征提取能力（通过backend/features/yamnet_extract.py封装实现）和 MusicGen 的音乐生成能力，让非专业用户无需掌握音乐理论即可完成风格转换

- **2.处理效率低**：通过backend/inference/full_pipeline.py中的FullMusicPipeline类实现分析 - 生成全流程自动化，将传统需要数小时的编曲工作缩短至分钟级

- **3.效果不稳定**：引入backend/inference/evaluate_generated.py中的评估体系，从风格增益、情绪增益、原始风格脱离度等多维度量化转换效果，确保输出质量

系统融合前端交互（核心界面frontend/src/views/Home.vue）、后端 API 服务（backend/server.py）与深度学习推理 pipeline，既实现了对音频处理与生成技术的工程化落地，也为音乐创意表达提供了新的技术范式。通过 IndexedDB 实现的本地数据持久化（前端存储方案）和MC_DEV_MODE=1的开发者模式，进一步降低了技术验证与二次开发的门槛。

# 功能亮点

- **多格式支持**：上传 WAV/MP3（或任何 `librosa` 支持的格式）并直接在浏览器中试听。
- **智能分析**：运行风格与情绪识别模型（YAMNet + 自定义分类器），返回概率分布，方便可视化与后续决策。
- **生成式转换**：选择目标风格/情绪后，触发异步音乐生成任务（基于 MusicGen），完成后可下载或播放结果。
- **持久化体验**：前端使用 IndexedDB 缓存上传与任务状态，刷新页面也不会丢失。
- **开发者友好**：`MC_DEV_MODE=1` 可启用 DEV 模式，快速返回伪造但稳定的数据，方便无 GPU 的前端联调。

# 技术实现

## 主要内容

- **前端**（`frontend/`）：核心界面 `src/views/Home.vue`，负责上传音频、渲染任务进度、展示结果，并提供目标风格与情绪的选择控件。
- **后端**（`backend/`）：`server.py` 提供 API、管理后台任务，并加载 `backend/inference/full_pipeline.py` 的 `FullMusicPipeline`，支持风格与情绪的分析与生成。
- **模型栈**：PyTorch (MusicGen)、TensorFlow (YAMNet)、Transformers、librosa 等依赖列于 `backend/requirements.txt`。

## 目录概览

```
music-converter/
├── backend/
│   ├── server.py — FastAPI 应用入口，定义路由、CORS、任务队列与文件输出路径
│   ├── requirements.txt — 后端 Python 依赖
│   ├── features/ — 音频特征提取相关代码目录
│   │   └── yamnet_extract.py — 封装 YAMNet，提供 embedding 与类别概率提取
│   ├── inference/ — 推理与生成管线核心模块（分析 → 提示 → 生成 → 后处理）
│   │   ├── full_pipeline.py — `FullMusicPipeline`：协调分析、提示构建与生成的高阶类
│   │   ├── generate_music.py — 与 MusicGen 交互，加载模型并保存生成音频
│   │   ├── analyze.py — 组合分析流程，调用特征提取与分类器并组织输出
│   │   ├── emotion_recognition.py — 情绪识别封装，返回情绪标签与置信度
│   │   ├── melody_extractor.py — 提取主旋律/音高序列的工具
│   │   ├── melody_scorer.py — 对旋律或生成结果做相似度/质量评分
│   │   ├── melody_transformer.py — 将旋律变换为目标风格的逻辑
│   │   ├── prompt_builder.py — 构建传给 MusicGen 的 prompt
│   │   └── style_recognition.py — 风格识别封装，返回风格标签及置信度
│   ├── models/ — 模型存放（可离线放置模型权重）
│   │   ├── yamnet/ — YAMNet 离线模型
│   │   └── ... 
│   └── utils/ — 各类辅助函数
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   └── Home.vue — 主页面
│   │   ├── api/
│   │   │   ├── index.js — API 基础客户端，配置 `baseURL` 与统一请求封装
│   │   │   ├── emotion.js — 封装获取情绪标签的调用
│   │   │   └── upload.js — 封装文件上传、启动转换与查询任务状态的 API
│   │   └── ...
│   └── ...
└── ...
```

## 环境要求

- **操作系统**：Windows / macOS / Linux (推荐 Ubuntu 22.04)。
- **Node.js**：`^20.19.0` 或 `>=22.12.0`。
- **Python**：3.10 及以上（强烈推荐使用 Conda 管理）。
- **硬件**：
  - **内存**：建议 **16GB** 以上（同时加载 TF 和 PyTorch 模型较耗内存）。
  - **GPU**：支持 CUDA 的 NVIDIA 显卡（8GB+ 显存），以便秒级完成生成任务。纯 CPU 亦可运行但较慢。
- **系统工具**：FFmpeg（必须安装，用于音频处理）。

## 本地测试

### 后端设置

请先准备好 Python 3.10+ 环境（推荐使用 Conda）。

**第一步：进入目录并创建环境**

```bash
cd backend

# [通用] 使用 Conda 创建环境
conda create -n mc-env python=3.10 -y
conda activate mc-env
```

**如果不使用 Conda，也可以使用 `venv`**

Windows: 
```
python -m venv venv
venv\Scripts\activate
```
macOS/Linux: 
```
python -m venv venv
source venv/bin/activate
```

**第二步：安装系统依赖 (仅 Linux)**

Windows 和 macOS 用户通常不需要此步骤，除非缺少 FFmpeg。

```bash
# Ubuntu/Debian 示例
sudo apt update && sudo apt install -y ffmpeg git
```

**第三步：安装 Python 依赖**

```bash
pip install -r requirements.txt
```

**第四步：启动后端服务**

根据你的操作系统选择对应的命令。

**Windows (CMD / PowerShell)**

```powershell
# [可选] 启用 DEV 模式 (跳过模型加载，适合无 GPU 调试)
set MC_DEV_MODE=1

# 启动服务
uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```

**macOS / Linux**

```bash
# [可选] 启用 DEV 模式 (跳过模型加载，适合无 GPU 调试)
export MC_DEV_MODE=1

# 启动服务
uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```

终端出现 `INFO: Application startup complete.` 即代表后端就绪。

> **模型下载提示**：首次启动会自动下载模型。若网络受限，请参考下文“环境变量”设置 `HF_ENDPOINT` 镜像，或手动下载 YAMNet 模型。

### 前端设置

确保已安装 Node.js (v20+)。

**第一步：安装依赖**

```bash
cd frontend
npm install
```

**第二步：启动开发服务器**

```bash
npm run dev
```

默认访问地址：`http://localhost:5173`。

### API测试

本地调试时，先确保后端已启动并监听 `http://localhost:8000`，再启动前端并通过浏览器访问 `http://localhost:5173` 进行交互测试。

- 浏览器测试：上传音频并观察任务进度、情绪/风格预测与生成结果。

- 命令行（curl）示例：

1) 健康检查
```bash
curl http://localhost:8000/health
```

2) 请求音频特征（分析）
```bash
curl -X POST -F "file=@/path/to/audio.wav" http://localhost:8000/api/features
```

3) 发起转换任务（异步）
```bash
curl -X POST -F "file=@/path/to/audio.wav" -F "style=pop" -F "emotion=happy" http://localhost:8000/api/convert
```

4) 查询任务状态
```bash
curl http://localhost:8000/api/tasks/01234567
```

## 部署说明

### 后端部署

在服务器上长期运行时，建议配合 `nohup` 和 Nginx。

1. **激活环境**：`source venv/bin/activate` 或 `conda activate mc-env`
2. **启动服务 (后台运行)**：
   **注意**：请在项目根目录（`music-converter`）下运行，以确保模块路径正确。
   ```sh
   # 示例：后台启动并将日志输出到 server.log
   nohup python3 -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
   ```
3. **Nginx 反向代理 (推荐)**：
   建议配置 Nginx 处理 HTTPS 及大文件上传限制。
   ```nginx
   server {
       listen 80;
       server_name api.your-domain.com;
       location / {
           proxy_pass http://127.0.0.1:8000;
           client_max_body_size 50M; # 允许大音频文件
       }
   }
   ```

### 前端部署

**方式 A：自动化部署 (推荐 - Vercel / Netlify / Railway)**
1. 将代码推送至 GitHub/GitLab。
2. 在 Vercel 或 Netlify 等平台导入本项目。
3. **关键配置**：在部署平台的 **Environment Variables** (环境变量) 设置中，请务必修改/添加 API Base URL 配置，使其指向你的生产环境后端 HTTPS 地址（例如 `https://api.your-domain.com`）。

**方式 B：手动构建 (Nginx 静态托管)**
```sh
cd frontend
npm run build
# 构建产物位于 frontend/dist
```
构建完成后，可将 `dist` 目录内的文件上传至 Nginx 的静态资源目录 (`/var/www/html`) 或其他静态托管服务。

## API 说明

| 方法 | 路径 | 功能 |
|------|------|------|
| `GET` | `/` | 返回简单 HTML，确认后端在线 |
| `GET` | `/health` | 健康检查，返回 `ok` |
| `GET` | `/api/styles` | 返回可用风格标签 |
| `GET` | `/api/emotions` | 返回可用情绪标签 |
| `POST` | `/api/features` | 上传音频 `file`，返回风格/情绪预测及概率 |
| `POST` | `/api/convert` | 上传音频并指定目标风格/情绪，启动异步转换 |
| `GET` | `/api/tasks/{task_id}` | 查询任务状态（`pending`/`processing`/`success`/`failed`） |
| `GET` | `/api/tasks/{task_id}/download` | 任务成功后下载生成的 WAV |

### 异步任务

1. 前端调用 `/api/convert` 上传音频。
2. 后端将任务写入内存 `TASKS`，后台线程调用 `FullMusicPipeline.process`。
3. 前端轮询 `/api/tasks/{task_id}`。
4. 状态变为 `success` 时，调用下载接口获取结果文件。

### 响应字段

- `task_id`: 内部任务 id，用于查询状态与下载。
- `status`: `pending` / `processing` / `success` / `failed`。
- `message`: 可选的错误或进度信息。
- `result.file`: 下载链接（若 `status === success`）。

### 环境变量
- `MC_DEV_MODE`: 设置为 `1` 时启用 DEV 模式，返回伪造数据并跳过模型加载。
- `HF_ENDPOINT`: 指定 Hugging Face 镜像地址用于模型下载。
- `ALLOW_ORIGINS`: 可指定前端允许的 CORS 域列表（在 `server.py` 中解析）。
- `PORT`: 服务端口（默认 8000）。

## 故障排查

- **下载模型报错 `Connection refused` / `Network unreachable`**：
  服务器无法连接 Hugging Face 或 TFHub。请设置 `HF_ENDPOINT` 环境变量，或手动下载 YAMNet 模型至 `backend/models/yamnet/` 目录。
- **启动时显示 `Killed`**：
  内存不足 (OOM)。请检查 Swap 是否开启，或升级服务器内存。
- **`No module named backend.server`**：
  运行路径错误。请退回到项目根目录，使用 `python3 -m uvicorn backend.server:app` 启动。
- **前端 CORS 错误**：
  检查前端域名是否已添加到 `server.py` 的 `allow_origins` 列表。
- **Mixed Content 错误**：
  前端是 HTTPS，后端是 HTTP。请配置 Nginx + SSL 证书，使后端支持 HTTPS。
- **上传失败 / 413 Payload Too Large**：
  Nginx 或前端上传配置可能限制了文件大小。请检查 Nginx 的 `client_max_body_size` 和前端的上传限制。
- **权限/路径错误**：
  `backend/output` 目录需要有写入权限（进程用户）。若发生权限错误，改变目录权限或修改 `server.py` 中的输出路径。

# 价值与展望

# 第三方说明

本项目核心依赖于以下深度学习模型与框架。若打算分发本项目或其中的模型权重，请务必查看上游项目的许可证（LICENSE）并在发布中包含必要的 LICENSE/NOTICE 文件。

## 核心模型

- **YAMNet (TensorFlow Hub)**
  - **用途**：音频事件分类与特征提取。本项目使用 YAMNet 提取音频的 Embeddings 特征，用于后续的情绪与风格分析。
  - **来源**：[TensorFlow Hub - YAMNet](https://tfhub.dev/google/yamnet/1)
  - **许可**：Apache 2.0
  - **说明**：项目中如需离线使用，请将模型放置于 [backend/models/yamnet/](backend/models/yamnet/)（目录下应包含 `saved_model.pb`、`variables/`、`assets/yamnet_class_map.csv` 等文件）。

- **MusicGen (Meta AI / Hugging Face)**
  - **用途**：基于文本提示或音频提示生成高质量音乐。本项目利用 MusicGen 根据用户选择的目标情绪与风格生成新的编曲。
  - **来源**：[Hugging Face - Facebook/MusicGen](https://huggingface.co/facebook/musicgen-small) (默认为 small 版本，可配置)
  - **许可**：CC-BY-NC 4.0 (非商业用途) / MIT (视具体模型版本而定，请务必核实)
  - **说明**：模型权重通常由 `transformers` 库自动下载并缓存。

## 基础框架

- **TensorFlow / tensorflow-hub**：用于加载与运行 YAMNet 模型。
- **PyTorch**：用于运行 MusicGen 生成模型。
- **Hugging Face Transformers**：提供 MusicGen 的加载接口与预训练权重管理。
- **Librosa**：用于音频信号处理、加载与特征预处理。
- **FFmpeg**：底层音频编解码支持（系统级依赖）。

# 写在最后

这个项目由小组的五位成员共同完成。

@dieWehmut @spacewolf28 @NanXiang-git @lsw6132 @XiaoYang-Zhou
