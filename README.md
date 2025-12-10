# Music Converter项目说明

## 项目简介
Music Converter 是一套端到端的音乐情绪/风格转换实验项目。用户上传受支持的音频（WAV、MP3 等），系统先解析其风格与情绪特征，再依据目标风格与情绪生成新的编曲。前端由 Vue 3 + Vite 驱动，后端使用 FastAPI，对接深度学习推理管线。

## 目录

- 项目简介
- 功能亮点
- 架构概览
- 环境要求
- 安装与配置
- 本地测试指南（含前后端步骤）
- 后端服务说明
- 前端运行与构建（含生产构建)
- API 说明与异步任务流程
- 开发提示
- 故障排查

-## 功能亮点

- 上传 WAV/MP3（或任何 `librosa` 支持的格式）并直接在浏览器中试听。
- 运行风格与情绪识别模型，返回概率分布，方便可视化与后续决策。
- 选择目标风格/情绪后，触发异步音乐生成任务，完成后可下载或播放结果。
- 前端使用 IndexedDB 缓存上传与任务状态，刷新页面也不会丢失。
- `MC_DEV_MODE=1` 可启用 DEV 模式，快速返回伪造但稳定的数据，方便无 GPU 的前端联调。


## 架构概览

- **前端**（`frontend/`）：核心界面 `src/views/Home.vue`，负责上传音频、渲染任务进度、展示结果，并提供目标风格与情绪的选择控件。
- **后端**（`backend/`）：`server.py` 提供 API、管理后台任务，并加载 `backend/inference/full_pipeline.py` 的 `FullMusicPipeline`，支持风格与情绪的分析与生成。
- **模型栈**：PyTorch、TensorFlow、Transformers、librosa 等依赖列于 `backend/requirements.txt`。

## 环境要求

- Node.js `^20.19.0` 或 `>=22.12.0`。
- Python 3.10 及以上，建议使用conda，也可以用venv/virtualenv。
- 支持 CUDA 的 GPU，以便更快完成生成任务。
- FFmpeg（可处理更多音频格式，推荐安装）。

## 安装与配置

推荐优先使用 Conda 管理后端 Python 环境（更方便管理 Python 版本与依赖）。如果无法使用 Conda，可退回使用 `venv`。

Windows (推荐 - Conda):

```cmd
cd backend
conda create -n mc-env python=3.10 -y
conda activate mc-env
pip install -r requirements.txt
```

macOS / Linux (推荐 - Conda):

```bash
cd backend
conda create -n mc-env python=3.10 -y
conda activate mc-env
pip install -r requirements.txt
```

备选：使用 `venv`（Windows 示例，macOS/Linux 将 `activate` 命令替换为 `source .venv/bin/activate`）：

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 前端依赖

进入 `frontend` 并安装依赖：

```bash
cd frontend
npm install
```

> 如仅需调试界面，可启用 DEV 模式（无需重型 ML 依赖），后端会返回稳定的伪数据以便前端联调。

## 本地测试指南

### 测试后端

1. 进入 `backend` 并激活虚拟环境：
   - Windows：`cd backend && .venv\Scripts\activate`
   - macOS/Linux：`cd backend && source .venv/bin/activate`
1. 若尚未安装完整 ML 依赖，可启用 DEV 模式：
   - Windows：`set MC_DEV_MODE=1`
   - macOS/Linux：`export MC_DEV_MODE=1`
   DEV 模式会返回伪造但稳定的分析/转换结果。
1. 启动服务：

   ```sh
   uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
   ```
1. 使用 curl 验证：
   - `curl http://localhost:8000/health` → `ok`
   - `curl http://localhost:8000/api/styles`
   - `curl http://localhost:8000/api/emotions`
   - `curl -F "file=@test.wav" http://localhost:8000/api/features`
1. 终端出现 `INFO:     Application startup complete.` 即代表后端就绪。

### 测试前端

1. 确保后端运行在 `http://localhost:8000`。
1. 新开终端进入 `frontend` 目录并执行：

   ```sh
   npm run dev
   ```
   默认开发地址为 `http://localhost:5173`。
1. 浏览器访问页面，上传音频并观察“特征提取”“转换”进度与结果。
1. 需对照调试时，可在提交转换后执行 `curl http://localhost:8000/api/tasks/<taskId>` 轮询状态。
1. 仅调 UI 时可保持 DEV 模式，让后端即时返回伪数据。

## 后端服务说明

1. 激活环境：`cd backend && .venv\Scripts\activate`（或 `source .venv/bin/activate`）。
2. （可选）开启 DEV 模式：`set/export MC_DEV_MODE=1`。
3. 启动服务：

   ```sh
   uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
   ```
4. API 默认监听 `http://localhost:8000`，并允许 `http://localhost:5173` 等常见前端来源。

## 前端运行与构建

```sh
cd frontend
npm run dev
```
- 若需要生产包：

   ```sh
   npm run build
   npm run preview  # 本地预览 dist
   ```

- 构建产物位于 `frontend/dist`，可部署到 Vercel、Netlify、任意静态站点。

## API 说明

| 方法 | 路径 | 功能 |
|------|------|------|
| `GET` | `/` | 返回简单 HTML，确认后端在线 |
| `GET` | `/health` | 健康检查，返回 `ok` |
| `GET` | `/api/styles` | 返回可用风格标签（若模型缺失则使用备选列表） |
| `GET` | `/api/emotions` | 返回可用情绪标签（若模型缺失则使用备选列表） |
| `POST` | `/api/features` | 上传音频 `file`，返回风格/情绪预测及概率 |
| `POST` | `/api/convert` | 上传音频并指定目标风格/情绪，启动异步转换 |
| `GET` | `/api/tasks/{task_id}` | 查询任务状态（`pending`/`processing`/`success`/`failed`） |
| `GET` | `/api/tasks/{task_id}/download` | 任务成功后下载生成的 WAV |

### 示例：`GET /api/emotions`

示例响应（JSON 数组）：

```json
["happy", "sad", "angry", "calm", "energetic"]
```

### 异步任务流程

1. 前端调用 `/api/convert` 上传音频。
2. 后端将任务写入内存 `TASKS`，后台线程调用 `FullMusicPipeline.process`。
3. 前端轮询 `/api/tasks/{task_id}`。
4. 状态变为 `success` 时，调用下载接口获取结果文件。

## 开发提示

- IndexedDB 缓存逻辑位于 `frontend/src/views/Home.vue`，可避免刷新导致任务丢失。
- 生成文件默认写入 `backend/output/<task_id>/`，请自行清理历史数据。
- `backend/inference/` 内含分析、旋律处理等辅助脚本，便于扩展能力。
- 需要更详细日志可使用 `uvicorn --log-level debug` 或自定义 `server.py` 中的 `LOG`。

## 故障排查

- **缺少 torch / tensorflow**：确认已执行 `pip install -r requirements.txt`，或启用 DEV 模式跳过真实推理。
- **任务下载提示 not ready**：说明后台仍在运行，请持续轮询任务状态。
- **CORS 错误**：检查前端地址是否在 `server.py` 的 `allow_origins` 列表。
- **大文件上传失败**：检查代理/云服务限制，可考虑分片或流式上传。

## Third-Party Notice

This project uses and/or depends on several third-party open-source libraries and models. If you plan to distribute the project or any model weights, please review the upstream licenses and include the appropriate LICENSE/NOTICE files.

- YAMNet (TensorFlow Hub): Source: <https://tfhub.dev/google/yamnet/1>. Notes: YAMNet is a model provided via TensorFlow Hub. Check the upstream page for the exact license (often Apache 2.0).

- TensorFlow: Source: <https://www.tensorflow.org/>. License: Typically Apache License 2.0. Verify the version you depend on.

- PyTorch (torch / torchvision / torchaudio): Source: <https://pytorch.org/>. Notes: Check the official repository and LICENSE for each package.

- Hugging Face Transformers / hub: Source: <https://github.com/huggingface/transformers>. License: Apache License 2.0 (verify for specific models you use).

- librosa: Source: <https://github.com/librosa/librosa>. License: ISC

- Other dependencies: See `backend/requirements.txt` for a full list (e.g. numpy, scipy, soundfile, huggingface-hub, tokenizers, etc.).
