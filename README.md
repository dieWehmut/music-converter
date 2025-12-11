# Music Converter 项目说明

## 项目简介

Music Converter 是一套端到端的音乐情绪/风格转换实验项目。用户上传受支持的音频（WAV、MP3 等），系统先解析其风格与情绪特征，再依据目标风格与情绪生成新的编曲。前端由 Vue 3 + Vite 驱动，后端使用 FastAPI，对接深度学习推理管线。

## 目录

- [Music Converter 项目说明](#music-converter-项目说明)
  - [项目简介](#项目简介)
  - [目录](#目录)
  - [功能亮点](#功能亮点)
  - [架构概览](#架构概览)
  - [环境要求](#环境要求)
  - [安装与配置](#安装与配置)
    - [1. 基础环境准备 (Linux/Ubuntu 示例)](#1-基础环境准备-linuxubuntu-示例)
    - [2. 后端环境 (Backend)](#2-后端环境-backend)
    - [3. 模型下载说明 (重要)](#3-模型下载说明-重要)
  - [前端依赖](#前端依赖)
  - [本地测试指南](#本地测试指南)
    - [测试后端](#测试后端)
    - [测试前端](#测试前端)
    - [常见 API 示例（curl）](#常见-api-示例curl)
  - [后端服务说明 (生产环境部署)](#后端服务说明-生产环境部署)
  - [前端运行与构建](#前端运行与构建)
  - [API 说明与异步任务流程](#api-说明与异步任务流程)
    - [异步任务流程](#异步任务流程)
    - [响应字段说明](#响应字段说明)
    - [环境变量清单（常用）](#环境变量清单常用)
  - [开发提示](#开发提示)
  - [故障排查](#故障排查)
  - [Third-Party Notice](#third-party-notice)

## 功能亮点

- **多格式支持**：上传 WAV/MP3（或任何 `librosa` 支持的格式）并直接在浏览器中试听。
- **智能分析**：运行风格与情绪识别模型（YAMNet + 自定义分类器），返回概率分布，方便可视化与后续决策。
- **生成式转换**：选择目标风格/情绪后，触发异步音乐生成任务（基于 MusicGen），完成后可下载或播放结果。
- **持久化体验**：前端使用 IndexedDB 缓存上传与任务状态，刷新页面也不会丢失。
- **开发者友好**：`MC_DEV_MODE=1` 可启用 DEV 模式，快速返回伪造但稳定的数据，方便无 GPU 的前端联调。

## 架构概览

- **前端**（`frontend/`）：核心界面 `src/views/Home.vue`，负责上传音频、渲染任务进度、展示结果，并提供目标风格与情绪的选择控件。
- **后端**（`backend/`）：`server.py` 提供 API、管理后台任务，并加载 `backend/inference/full_pipeline.py` 的 `FullMusicPipeline`，支持风格与情绪的分析与生成。
- **模型栈**：PyTorch (MusicGen)、TensorFlow (YAMNet)、Transformers、librosa 等依赖列于 `backend/requirements.txt`。

## 环境要求

- **操作系统**：Windows / macOS / Linux (推荐 Ubuntu 22.04)。
- **Node.js**：`^20.19.0` 或 `>=22.12.0`。
- **Python**：3.10 及以上（强烈推荐使用 Conda 管理）。
- **硬件**：
  - **内存**：建议 **16GB** 以上（同时加载 TF 和 PyTorch 模型较耗内存）。
  - **GPU**：支持 CUDA 的 NVIDIA 显卡（8GB+ 显存），以便秒级完成生成任务。纯 CPU 亦可运行但较慢。
- **系统工具**：FFmpeg（必须安装，用于音频处理）。

## 安装与配置

### 1. 基础环境准备 (Linux/Ubuntu 示例)

```bash
# 更新系统并安装 FFmpeg
sudo apt update && sudo apt install -y ffmpeg git

# [建议] 开启 Swap 虚拟内存 (防止 16G 内存爆满被系统杀进程)
sudo fallocate -l 8G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 2. 后端环境 (Backend)

推荐优先使用 Conda 管理后端 Python 环境。如果无法使用 Conda，可退回使用 `venv`。

**方案 A: 使用 Conda (推荐)**

```bash
cd backend
conda create -n mc-env python=3.10 -y
conda activate mc-env

# [可选] 配置国内镜像源加速下载 (阿里云示例)
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 安装依赖
# 提示: 若服务器无 GPU，可指定下载 CPU 版 PyTorch 以节省空间
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

**方案 B: 使用 venv**

```bash
cd backend
python3 -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 模型下载说明 (重要)

系统在首次启动时会自动下载所需模型。**但在网络受限的环境下（如国内服务器），可能会出现连接超时。**

- **Hugging Face (MusicGen)**:
  如果无法连接，可在启动前设置环境变量使用镜像：
  `export HF_ENDPOINT=https://hf-mirror.com`

- **YAMNet (TensorFlow Hub)**:
  如果服务器无法访问 Google (tfhub.dev)，请手动下载模型并放入指定目录，**系统会自动检测并优先加载本地文件**。
  1. 下载 [yamnet_1.tar.gz](https://storage.googleapis.com/tfhub-modules/google/yamnet/1.tar.gz)。
  2. 解压至 `backend/models/yamnet/`。
  3. 确保目录结构为：`backend/models/yamnet/saved_model.pb`。

注意：在 `MC_DEV_MODE=1` 时，系统会返回伪造的分析结果，从而跳过模型加载，适合无 GPU 或受限网络环境下的前端调试。

## 前端依赖

进入 `frontend` 并安装依赖：

```bash
cd frontend
npm install
```

> 如仅需调试界面，可启用 DEV 模式（无需重型 ML 依赖），后端会返回稳定的伪数据以便前端联调。

## 本地测试指南

### 测试后端

1. 进入 `backend` 并激活虚拟环境。
2. 若尚未安装完整 ML 依赖，可启用 DEV 模式：
   - Windows：`set MC_DEV_MODE=1`
   - macOS/Linux：`export MC_DEV_MODE=1`
3. 启动服务：
   ```sh
   uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
   ```
4. 使用 curl 验证：
   - `curl http://localhost:8000/health` → `ok`
5. 终端出现 `INFO: Application startup complete.` 即代表后端就绪。

### 测试前端

1. 确保后端运行在 `http://localhost:8000`。
2. 新开终端进入 `frontend` 目录并执行：
   ```sh
   npm run dev
   ```
   默认开发地址为 `http://localhost:5173`。
3. 浏览器访问页面测试功能。

### 常见 API 示例（curl）

1) 健康检查
```bash
curl http://localhost:8000/health
```

2) 请求音频特征（分析）
```bash
curl -X POST -F "file=@/path/to/audio.wav" http://localhost:8000/api/features
```
返回示例：
```
{
  "styles": [{"name": "pop", "prob": 0.62}],
  "emotions": [{"name": "happy", "prob": 0.81}],
  "duration": 12.5
}
```

3) 发起转换任务（异步）
```bash
curl -X POST -F "file=@/path/to/audio.wav" -F "style=pop" -F "emotion=happy" http://localhost:8000/api/convert
```
返回示例：
```
{
  "task_id": "01234567",
  "status": "pending",
  "message": "Processing started"
}
```

4) 查询任务状态
```bash
curl http://localhost:8000/api/tasks/01234567
```
返回示例：
```
{
  "task_id": "01234567",
  "status": "success",
  "result": {
    "file": "/api/tasks/01234567/download",
    "duration": 15.0
  }
}
```

## 后端服务说明 (生产环境部署)

在服务器上长期运行时，建议配合 `nohup` 和 Nginx。

1. **激活环境**：`source venv/bin/activate`
2. **启动服务 (后台运行)**：
   **注意**：请在项目根目录（`music-converter`）下运行，以确保模块路径正确。
   ```sh
   # 示例：后台启动并将日志输出到 server.log
   nohup python3 -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
   ```
3. **查看日志**：`tail -f server.log`
4. **Nginx 反向代理 (推荐)**：
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

## 前端运行与构建

```sh
cd frontend
npm run dev
```

- **生产部署 (自动化/手动)**：

   **方式 A：自动化部署 (推荐 - Vercel / Netlify / Railway)**
   无需在本地手动运行 `build` 命令。
   1. 将代码推送至 GitHub/GitLab。
   2. 在 Vercel 或 Netlify 等平台导入本项目。
   3. 平台会自动识别 `package.json` 中的构建命令并完成部署。
   4. **关键配置**：在部署平台的 **Environment Variables** (环境变量) 设置中，请务必修改/添加 API Base URL 配置，使其指向你的生产环境后端 HTTPS 地址（例如 `https://api.your-domain.com`）。

   **方式 B：手动构建 (Nginx 静态托管)**
   ```sh
   npm run build
   # 构建产物位于 frontend/dist
   ```
   构建完成后，可将 `dist` 目录内的文件上传至 Nginx 的静态资源目录 (`/var/www/html`) 或其他静态托管服务。
   **注意**：手动构建前，请确保配置文件中的 API 地址已指向正确的生产环境后端。
   ```

## API 说明与异步任务流程

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

### 异步任务流程

1. 前端调用 `/api/convert` 上传音频。
2. 后端将任务写入内存 `TASKS`，后台线程调用 `FullMusicPipeline.process`。
3. 前端轮询 `/api/tasks/{task_id}`。
4. 状态变为 `success` 时，调用下载接口获取结果文件。

### 响应字段说明

- `task_id`: 内部任务 id，用于查询状态与下载。
- `status`: `pending` / `processing` / `success` / `failed`。
- `message`: 可选的错误或进度信息。
- `result.file`: 下载链接（若 `status === success`）。

### 环境变量清单（常用）
- `MC_DEV_MODE`: 设置为 `1` 时启用 DEV 模式，返回伪造数据并跳过模型加载。
- `HF_ENDPOINT`: 指定 Hugging Face 镜像地址用于模型下载。
- `ALLOW_ORIGINS`: 可指定前端允许的 CORS 域列表（在 `server.py` 中解析）。
- `PORT`: 服务端口（默认 8000）。

## 开发提示

- **IndexedDB 缓存**：位于 `frontend/src/views/Home.vue`，可避免刷新导致任务丢失。
- **文件清理**：生成文件默认写入 `backend/output/<task_id>/`，生产环境建议定期清理。
- **日志调试**：需要更详细日志可使用 `uvicorn --log-level debug` 或自定义 `server.py` 中的 `LOG`。

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
  - Nginx 或前端上传配置可能限制了文件大小。请检查 Nginx 的 `client_max_body_size` 和前端的上传限制（通常在 HTML `input` 或 JS 里设置）。

- **权限/路径错误**：
  - `backend/output` 目录需要有写入权限（进程用户）。若发生权限错误，改变目录权限或修改 `server.py` 中的输出路径。

- **内存不足（Killed）**：
  - 如果启动模型时出现 `Killed`，说明服务内存不足。建议增加 swap 或使用机器内存更大的环境，或者启用 `MC_DEV_MODE` 跳过模型加载。

## Third-Party Notice

This project uses and/or depends on several third-party open-source libraries and models. If you plan to distribute the project or any model weights, please review the upstream licenses and include the appropriate LICENSE/NOTICE files.

- YAMNet (TensorFlow Hub): Source: <https://tfhub.dev/google/yamnet/1>. License: Apache 2.0.
- TensorFlow: Source: <https://www.tensorflow.org/>. License: Apache 2.0.
- PyTorch (torch / torchvision / torchaudio): Source: <https://pytorch.org/>.
- Hugging Face Transformers / hub: Source: <https://github.com/huggingface/transformers>. License: Apache 2.0.
- librosa: Source: <https://github.com/librosa/librosa>. License: ISC.
- Other dependencies: See `backend/requirements.txt` for a full list.