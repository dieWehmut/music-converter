<h1 align="center">Music Converter</h1>

<div align="center">

<!-- 第一行：Colab 和 Demo -->
<div>
<a href="https://colab.research.google.com/github/dieWehmut/music-converter/blob/main/Colab-music-converter.ipynb" target="_blank">
  <img src="https://img.shields.io/badge/COLAB-OPEN_IN_COLAB-F9AB00?style=flat-square&logo=googlecolab&logoColor=white&labelColor=555555" alt="Open In Colab"/>
</a>
<a href="https://music-converter.hc-dsw-nexus.me/" target="_blank">
  <img src="https://img.shields.io/badge/DEMO-%E5%85%8D%E8%B4%B9%E5%9C%A8%E7%BA%BF%E4%BD%93%E9%AA%8C-F9D553?style=flat-square&logo=google-chrome&logoColor=white&labelColor=555555" alt="Online Demo">
</a>
</div>

<<<<<<< HEAD
<!-- 第二行：Python 和 License -->
=======
<!-- 第二行：Python、MusicGen Model 和 License -->
>>>>>>> c874920e640810b96189f8502876ab84f4a50610
<div>
<a href="https://www.python.org/">
  <img src="https://img.shields.io/badge/PYTHON-3.9+-blue?style=flat-square&logo=python&logoColor=white&labelColor=555555" alt="Python Version">
</a>
<<<<<<< HEAD
=======
<a href="https://huggingface.co/facebook/musicgen-small" target="_blank">
  <img src="https://img.shields.io/badge/MODEL-MusicGen-FFD21E?style=flat-square&logo=huggingface&logoColor=white&labelColor=555555" alt="Hugging Face Model">
</a>
>>>>>>> c874920e640810b96189f8502876ab84f4a50610
<a href="https://github.com/dieWehmut/music-converter/blob/main/LICENSE">
  <img src="https://img.shields.io/badge/LICENSE-MIT-green?style=flat-square&logo=github&logoColor=white&labelColor=555555" alt="License">
</a>
</div>

</div>

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
<<<<<<< HEAD
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
=======
  - [核心代码](#核心代码)
  - [目录概览](#目录概览)
  - [环境要求](#环境要求)
- [本地开发指南](#本地开发指南)
  - [后端设置](#后端设置)
  - [前端设置](#前端设置)
  - [本地联调与故障排查](#本地联调与故障排查)
- [部署运维指南](#部署运维指南)
  - [Docker部署 (推荐)](#docker部署-推荐)
  - [Colab运行](#colab运行)
  - [传统服务器部署 (Nginx + Nohup)](#传统服务器部署-nginx--nohup)
  - [前端构建部署](#前端构建部署)
  - [部署故障排查](#部署故障排查)
- [API 接口文档](#api-接口文档)
  - [核心接口](#核心接口)
  - [异步任务机制](#异步任务机制)
  - [环境变量配置](#环境变量配置)
- [价值与展望](#价值与展望)
  - [从“听觉”到“理解”：精准的提示词构建体系](#从听觉到理解精准的提示词构建体系)
  - [自动化“质检员”与闭环迭代](#自动化质检员与闭环迭代)
  - [解决生成模型的“长音频崩坏”难题](#解决生成模型的长音频崩坏难题)
  - [与传统方法的对比](#与传统方法的对比)
  - [未来展望](#未来展望)
>>>>>>> c874920e640810b96189f8502876ab84f4a50610
- [第三方说明](#第三方说明)
  - [核心模型](#核心模型)
  - [基础框架](#基础框架)
- [写在最后](#写在最后)

</details>

# 项目简介

Music Converter 是一套端到端的音乐情绪/风格转换实验项目。用户上传受支持的音频（WAV、MP3 等），系统先解析其风格与情绪特征，再依据目标风格与情绪生成新的编曲。前端由 Vue 3 + Vite 驱动，后端使用 FastAPI，对接深度学习推理管线。

# 项目背景
随着数字音乐产业的蓬勃发展，用户对音乐个性化改编的需求日益增长。传统音乐风格往往依赖专业音乐人手动创作，成本高、周期长，难以满足普通用户快速变化的多样化需求。尤其在风格迁移与情绪转换场景中，需要同时兼顾原曲旋律特征与目标风格的融合，传统人工制作方式难以高效实现批量处理。

本项目旨在通过深度学习技术，构建一套自动化的音乐情绪与风格转换系统，核心解决三大痛点：

<<<<<<< HEAD
- **1.技术门槛高**：借助 YAMNet 模型的音频特征提取能力（通过backend/features/yamnet_extract.py封装实现）和 MusicGen 的音乐生成能力，让非专业用户无需掌握音乐理论即可完成风格转换

- **2.处理效率低**：通过backend/inference/full_pipeline.py中的FullMusicPipeline类实现分析 - 生成全流程自动化，将传统需要数小时的编曲工作缩短至分钟级

- **3.效果不稳定**：引入backend/inference/evaluate_generated.py中的评估体系，从风格增益、情绪增益、原始风格脱离度等多维度量化转换效果，确保输出质量

系统融合前端交互（核心界面frontend/src/views/Home.vue）、后端 API 服务（backend/server.py）与深度学习推理 pipeline，既实现了对音频处理与生成技术的工程化落地，也为音乐创意表达提供了新的技术范式。通过 IndexedDB 实现的本地数据持久化（前端存储方案）和MC_DEV_MODE=1的开发者模式，进一步降低了技术验证与二次开发的门槛。
=======
- **1.技术门槛高**：借助 YAMNet 模型的音频特征提取能力（通过 `backend/features/yamnet_extract.py` 封装实现）和 MusicGen 的音乐生成能力，让非专业用户无需掌握音乐理论即可完成风格转换。

- **2.处理效率低**：通过 `backend/inference/full_pipeline.py` 中的 `FullMusicPipeline` 类实现分析 - 生成全流程自动化，将传统需要数小时的编曲工作缩短至分钟级。

- **3.效果不稳定**：引入 `backend/inference/evaluate_generated.py` 中的评估体系，从风格增益、情绪增益、原始风格脱离度等多维度量化转换效果，确保输出质量。

系统融合前端交互（核心界面 、后端 API 服务与深度学习推理 pipeline，既实现了对音频处理与生成技术的工程化落地，也为音乐创意表达提供了新的技术范式。
>>>>>>> c874920e640810b96189f8502876ab84f4a50610

# 功能亮点

- **多格式支持**：上传 WAV/MP3（或任何 `librosa` 支持的格式）并直接在浏览器中试听。
- **智能分析**：运行风格与情绪识别模型（YAMNet + 自定义分类器），返回概率分布，方便可视化与后续决策。
- **生成式转换**：选择目标风格/情绪后，触发异步音乐生成任务（基于 MusicGen），完成后可下载或播放结果。
<<<<<<< HEAD
- **持久化体验**：前端使用 IndexedDB 缓存上传与任务状态，刷新页面也不会丢失。
- **开发者友好**：`MC_DEV_MODE=1` 可启用 DEV 模式，快速返回伪造但稳定的数据，方便无 GPU 的前端联调。
=======
- **智能队列系统**：后端内置优先级队列，短任务（<20s）自动插队优先处理，长任务后台排队。
- **长音频支持**：通过自动化切片与拼接技术，突破 MusicGen 的 30s 生成限制，支持任意长度音频。
- **持久化体验**：前端使用 IndexedDB 缓存上传与任务状态，刷新页面也不会丢失。
>>>>>>> c874920e640810b96189f8502876ab84f4a50610

# 技术实现

## 主要内容

- **前端**（`frontend/`）：核心界面 `src/views/Home.vue`，负责上传音频、渲染任务进度、展示结果，并提供目标风格与情绪的选择控件。
- **后端**（`backend/`）：`server.py` 提供 API、管理后台任务，并加载 `backend/inference/full_pipeline.py` 的 `FullMusicPipeline`，支持风格与情绪的分析与生成。
- **模型栈**：PyTorch (MusicGen)、TensorFlow (YAMNet)、Transformers、librosa 等依赖列于 `backend/requirements.txt`。

<<<<<<< HEAD
## 目录概览

=======
## 核心代码

以下是项目关键模块的深度解读与核心逻辑展示：

**`backend/inference/full_pipeline.py` (业务管线)**
**功能**：处理长音频的分片（Slicing）与拼接（Stitching），突破模型输入长度限制。

```python
# 核心逻辑：超过30秒自动分片处理
for i in range(total_segments):
    # 1. 切出当前 30s 片段
    y_seg = y_full[start_sample:end_sample]
    
    # 2. 提取该片段的旋律特征
    seg_melody_path = self.melody_extractor.extract_melody_to_wav(..., y_seg)

    # 3. 单独生成该片段 (MusicGen)
    self.music_gen.generate_with_melody(
        prompt=prompt,
        melody_path=str(seg_trans_path),
        target_seconds=seg_duration  # 动态时长
    )
    
    # 4. 收集结果
    full_generated_audio.append(y_gen_seg)

# 5. 最后拼接所有片段
final_y = np.concatenate(full_generated_audio)
```

**`backend/inference/generate_music.py` (生成引擎)**
**功能**：内置后处理算法，修复 MusicGen 常见的“中段崩塌”（突然静音）和“尾部噪音”问题。

```python
# 核心逻辑：检测并修复音频中段能量塌陷
@staticmethod
def _mid_collapse_fix(audio, sr):
    N = len(audio)
    # 取中段样本
    a = audio[N//3 : N//2]
    b = audio[N//2 : 2*N//3]
    
    # 计算能量 (RMS)
    rms_a = np.sqrt(np.mean(a**2))
    rms_b = np.sqrt(np.mean(b**2))

    # 如果后半段能量骤降 (<33%)，则使用前半段进行 Crossfade 修复
    if rms_a > 1e-5 and rms_b < rms_a * 0.33:
        fixed = 0.7 * a[:len(b)] + 0.3 * b
        audio[N//2 : N//2+len(fixed)] = fixed
    
    return audio
```

**`backend/inference/prompt_builder.py` (提示词工程)**
**功能**：将数学特征评分转化为自然语言描述，动态构建 Prompt，而非使用死板的模板。

```python
# 核心逻辑：根据评分动态调整描述词
def describe_hook(self, hook_score):
    if hook_score > 0.45:
        return "a memorable melodic hook"      # 强 Hook
    elif hook_score > 0.25:
        return "a mildly recognizable hook"    # 中等
    else:
        return "a simple motif"                # 弱 Hook

def build_prompt(self, melody_info, style, ...):
    # 动态组装 Prompt
    return f"""
    ### Melody Characteristics
    - {self.describe_pitch_range(melody_info["pitch_range"])}
    - {self.describe_hook(melody_info["hook_score"])}
    
    ### Target Style
    Rewrite the music into **{style}** style.
    """
```

## 目录概览


>>>>>>> c874920e640810b96189f8502876ab84f4a50610
```
music-converter/
├── backend/
│   ├── server.py — FastAPI 应用入口，定义路由、CORS、任务队列与文件输出路径
│   ├── requirements.txt — 后端 Python 依赖
│   ├── features/ — 音频特征提取相关代码目录
│   │   └── yamnet_extract.py — 封装 YAMNet，提供 embedding 与类别概率提取
│   ├── inference/ — 推理与生成管线核心模块（分析 → 提示 → 生成 → 后处理）
│   │   ├── full_pipeline.py — 协调分析、提示构建与生成的高阶类
│   │   ├── generate_music.py — 与 MusicGen 交互，加载模型并保存生成音频
│   │   ├── analyze.py — 组合分析流程，调用特征提取与分类器并组织输出
│   │   ├── melody_extractor.py — 提取主旋律/音高序列的工具
│   │   ├── ...
│   │   └── prompt_builder.py — 构建传给 MusicGen 的 prompt
│   ├── models/ — 模型存放（可离线放置模型权重）
│   │   ├── ...
│   │   └── yamnet/ — YAMNet 离线模型
│   └── utils/ — 各类辅助函数
├── frontend/
│   ├── index.html
│   ├── ...
│   └── src/
│       ├── components/
│       ├── views/
│       │   └── Home.vue — 主页面
│       ├── ...
│       └──api/
│          ├── index.js — API 基础客户端，配置 `baseURL` 与统一请求封装
│          ├── emotion.js — 封装获取情绪标签的调用
│          └── upload.js — 封装文件上传、启动转换与查询任务状态的 API
├── ...
├── docs/ 
├── LICENSE 
├── Colab-music-converter.ipynb — Colab 笔记本，用于在线体验
├── Dockerfile — Docker 容器化配置
└── README.md — 项目说明文档
```

## 环境要求

- **操作系统**：Windows / macOS / Linux (推荐 Ubuntu 22.04)。
- **Node.js**：`^20.19.0` 或 `>=22.12.0`。
- **Python**：3.10 及以上（强烈推荐使用 Conda 管理）。
- **硬件**：
  - **内存**：建议 **16GB** 以上（同时加载 TF 和 PyTorch 模型较耗内存）。
  - **GPU**：支持 CUDA 的 NVIDIA 显卡（8GB+ 显存），以便秒级完成生成任务。纯 CPU 亦可运行但较慢。
- **系统工具**：FFmpeg（必须安装，用于音频处理）。

<<<<<<< HEAD
## 本地测试

### 后端设置

请先准备好 Python 3.10+ 环境（推荐使用 Conda）。

**第一步：进入目录并创建环境**
=======
# 本地开发指南

## 后端设置

请先准备好 Python 3.10+ 环境（推荐使用 Conda）。

**步骤 1：创建并激活环境**
>>>>>>> c874920e640810b96189f8502876ab84f4a50610

```bash
cd backend

# [通用] 使用 Conda 创建环境
conda create -n mc-env python=3.10 -y
conda activate mc-env
```
<<<<<<< HEAD

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
=======
> **预期输出**：终端前缀变为 `(mc-env)`。

**步骤 2：安装系统级依赖 (FFmpeg)**

*MusicGen 和 Librosa 处理音频必须依赖 FFmpeg。*

*   **Windows**: 下载 FFmpeg exe 并添加到环境变量 PATH。
*   **macOS**: `brew install ffmpeg`
*   **Ubuntu/Debian**:
    ```bash
    sudo apt update && sudo apt install -y ffmpeg git libsndfile1
    ```

**步骤 3：安装 Python 依赖**
>>>>>>> c874920e640810b96189f8502876ab84f4a50610

```bash
pip install -r requirements.txt
```
> **预期输出**：显示 `Successfully installed torch... tensorflow...` 等信息，无红色报错。

<<<<<<< HEAD
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

=======
**步骤 4：启动后端服务**

根据你的操作系统选择命令。

*   **Windows (CMD / PowerShell)**:
    ```powershell
    # [可选] 启用 DEV 模式 (跳过模型加载，适合无 GPU 调试前端交互)
    set MC_DEV_MODE=1
    # 启动服务
    uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
    ```

*   **macOS / Linux**:
    ```bash
    # [可选] 启用 DEV 模式
    export MC_DEV_MODE=1
    # 启动服务
    uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
    ```

> **预期输出**：
> ```text
> INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
> INFO:     Application startup complete.
> INFO:     🚀 Priority Worker started! ...
> ```

## 前端设置 

确保已安装 Node.js (v20+)。

**步骤 1：安装依赖**

>>>>>>> c874920e640810b96189f8502876ab84f4a50610
```bash
cd frontend
npm install
```

<<<<<<< HEAD
**第二步：启动开发服务器**
=======
**步骤 2：启动开发服务器**
>>>>>>> c874920e640810b96189f8502876ab84f4a50610

```bash
npm run dev
```
<<<<<<< HEAD

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

在服务器上长期运行时，建议配合 `nohup` 保持后台运行，并配置 Nginx 进行反向代理。

**前提**：请确保当前处于项目根目录（例如 `/root/music-converter`），而不是 `backend` 内部。

**启动服务 (标准流程)**

为了防止环境丢失导致 `ModuleNotFoundError`，建议按以下步骤操作：

```bash
# 1. 杀掉旧进程 (防止端口冲突)
pkill -f uvicorn

# 2. 激活虚拟环境 (根据你的安装方式选一个)
# Linux/macOS (venv):
source backend/venv/bin/activate
# Windows:
# backend\venv\Scripts\activate
# Conda:
# conda activate mc-env

# 3. 启动服务 (后台运行)
# 注意：必须加上 -m uvicorn 以确保 python 能找到包
nohup python3 -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

# ★ 稳妥启动技巧 (推荐) ★
# 如果发现 nohup 报错找不到模块，请直接指定虚拟环境 python 的绝对路径运行：
# nohup /path/to/venv/bin/python3 -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

**验证运行**

```bash
# 查看实时日志
tail -f server.log
```
当看到 `INFO: Application startup complete.` 时，说明服务启动成功。

**Nginx 反向代理 (推荐)**

建议配置 Nginx 处理 HTTPS、域名转发及大文件上传限制。

配置文件示例 (`/etc/nginx/conf.d/music-backend.conf`)：

```nginx
server {
    listen 80;
    server_name api.your-domain.com; # 替换为你的域名

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # [关键] 允许 50MB 音频文件上传，防止 413 Entity Too Large 错误
        client_max_body_size 50M; 
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

## 应用场景与潜力
本项目不仅是一个技术验证原型，在数字媒体与创意产业中具有广泛的应用潜力：

- **短视频与自媒体创作**：为视频创作者提供低成本的 BGM 生成方案。用户无需担心版权问题，即可将现有素材快速转换为符合视频氛围（如“欢快”、“悲伤”）的背景音乐。
- **音乐制作辅助（Demo 快速验证）**：辅助初级音乐制作人或作曲家。用户可以录制一段简单的哼唱或旋律，通过系统快速尝试不同的编曲风格（如从 Pop 转为 Jazz），激发创作灵感。
- **游戏与沉浸式体验**：在游戏开发中，根据玩家当前的场景情绪自动调整背景音乐风格，实现动态音频（Adaptive Audio）的低成本生成。
- **心理疗愈与个性化听感**：结合情绪识别技术，为用户生成符合当下心情或旨在调节心情的音乐，探索 AI 音乐疗法。

## 当前局限与不足
尽管本项目实现了端到端的转换流程，但在实际应用中仍存在以下挑战：

- **推理资源消耗大**：目前集成的 MusicGen 模型对 GPU 显存要求较高（建议 8GB+），在纯 CPU 环境下生成速度较慢，难以满足实时性要求极高的交互场景。
- **长音频一致性**：受限于模型上下文窗口，生成的音频目前多为短片段（10-30秒）。在生成更长时间的音乐时，可能会出现旋律结构松散或风格前后不一致的问题。
- **细粒度控制有限**：目前系统主要基于宏观的“情绪”和“风格”标签进行控制，尚不支持对特定乐器（如“只保留钢琴”）或特定节奏型进行精细化调整。

## 未来改进方向
针对上述不足，我们计划从以下维度进行优化：

- **模型轻量化与加速**：探索模型量化（Quantization）技术或引入更轻量级的生成模型（如 MusicGen-Small 的蒸馏版），降低部署门槛，提升生成速度。
- **丰富交互维度**：引入更多模态的输入控制，例如支持通过文字描述（Text-to-Music）与音频参考相结合的多模态 Prompt，让生成结果更精准。
- **云端部署与微服务化**：将推理模块独立为高性能微服务，配合 Celery + Redis 消息队列构建弹性伸缩的云端集群，以支持多用户并发访问。

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
=======
> **预期输出**：
> ```text
> VITE v5.x.x  ready in 300 ms
> ➜  Local:   http://localhost:5173/
> ```

## 本地联调与故障排查

1.  **浏览器访问**：打开 `http://localhost:5173`。
2.  **健康检查**：在浏览器或 Postman 访问 `http://localhost:8000/health`，应返回 `"ok"`。
3.  **常见问题**：
    *   **CORS 错误**：如果前端报错 Network Error，检查 `backend/server.py` 中的 `allow_origins` 列表是否包含 `http://localhost:5173`。
    *   **模型下载慢**：设置环境变量 `HF_ENDPOINT=https://hf-mirror.com`。
    *   **`libsndfile` 报错**：说明系统缺少音频库，请重新检查**步骤 2**的系统依赖安装。

# 部署运维指南

## Docker部署 (推荐)

本项目提供了标准的 `Dockerfile`，支持一键构建，环境隔离，最为推荐。

**步骤 1：构建镜像**

请在项目**根目录**（即包含 `Dockerfile` 的目录）下执行：

```bash
# 注意最后有一个点 "."
docker build -t music-converter:v1 -f Dockerfile .
```
> **预期输出**：构建过程会安装 ffmpeg 和 python 依赖，最后显示 `Successfully tagged music-converter:v1`。

**步骤 2：运行容器**

```bash
# 基础运行 (默认配置)
docker run -d -p 8000:8000 --name mc-server music-converter:v1

# 进阶运行 (启用长音频 + 挂载模型缓存 + 使用 GPU)
# 需先安装 nvidia-container-toolkit
docker run -d \
  -p 8000:8000 \
  --gpus all \
  -e MC_ENABLE_LONG_AUDIO=1 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --name mc-server \
  music-converter:v1
```

**步骤 3：验证**
查看日志确保服务启动成功：
```bash
docker logs -f mc-server
```

## Colab运行

适合没有本地显卡的用户，利用 Google 免费 T4 GPU。

1.  点击页面顶部的 **Open in Colab** 徽章。
2.  在 Colab 中，你需要一个 [Ngrok Authtoken](https://dashboard.ngrok.com/get-started/your-authtoken)。
3.  **按顺序执行 Notebook 单元格**：
    *   **Step 1**: 拉取代码。
    *   **Step 2**: 安装依赖。
    *   **Step 3**: 填入 Token 并启动。
4.  复制输出的 `Public URL` (如 `https://xxxx.ngrok-free.app`) 到前端配置中。

## 传统服务器部署 (Nginx + Nohup)

**步骤 1：启动后端**

```bash
cd /path/to/music-converter
source backend/venv/bin/activate
# 后台运行，日志输出到 server.log
nohup python3 -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

**步骤 2：配置 Nginx 反向代理**

编辑 `/etc/nginx/conf.d/music.conf`：

```nginx
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        # 关键：允许 100MB 上传，防止大音频被 Nginx 拦截
        client_max_body_size 100M;
        # 防止生成时间过长导致 Nginx 504 超时
        proxy_read_timeout 300s;
    }
}
```

## 前端构建部署

**步骤 1：构建**

```bash
cd frontend
# 确保 .env 或构建环境中 VITE_API_BASE 指向你的后端地址
npm run build
```

**步骤 2：静态托管**

将 `frontend/dist` 目录下的所有文件上传至 Nginx 的 `/var/www/html` 或部署到 Vercel/Netlify。

## 部署故障排查

-   **`413 Payload Too Large`**：
    *   原因：上传的音频超过了 Nginx 默认限制（1MB）。
    *   解决：在 Nginx 配置中添加 `client_max_body_size 100M;`。
-   **`SoundFileError: System error`**：
    *   原因：Docker 或 Linux 环境下路径解析问题。
    *   解决：本项目代码已在 `server.py` 中强制使用 `.resolve()` 绝对路径，请确保 Docker 容器有写入 `backend/output` 的权限。
-   **任务一直处于 `queued` 状态**：
    *   原因：后台 Worker 正在处理其他耗时任务（单线程消费者）。
    *   解决：耐心等待，或在 `server.py` 中增加 Worker 线程数（仅限显存充足时）。

# API 接口文档

## 核心接口

| 功能 | 方法 | 路径 | 参数 (Form Data) | 返回示例 |
| :--- | :--- | :--- | :--- | :--- |
| **健康检查** | `GET` | `/health` | 无 | `"ok"` |
| **获取风格** | `GET` | `/api/styles` | 无 | `{"styles": ["rock", "pop", ...]}` |
| **特征分析** | `POST` | `/api/features` | `file`: (Binary) | `{"style": "rock", "emotion": "happy", ...}` |
| **提交任务** | `POST` | `/api/convert` | `file`: (Binary)<br>`style`: (String)<br>`emotion`: (String) | `{"task_id": "uuid...", "status": "queued"}` |
| **查询状态** | `GET` | `/api/tasks/{id}` | 无 | `{"status": "processing", "msg": "..."}` |
| **下载结果** | `GET` | `/api/tasks/{id}/download` | 无 | 二进制 WAV 文件流 |

## 异步任务机制

为了防止长音频生成阻塞服务器，本项目采用 **异步轮询** 机制：

1.  **提交**：前端调用 `/api/convert`，后端将任务放入 `PriorityQueue`，立即返回 `task_id`。
2.  **排队**：后台 Worker 线程根据优先级（短任务优先）依次取出任务执行。
3.  **轮询**：前端每隔 2秒 调用 `/api/tasks/{id}` 查询状态。
    *   `queued`: 排队中
    *   `processing`: 生成中
    *   `success`: 完成，前端自动调用下载接口
    *   `failed`: 报错，前端展示错误信息

## 环境变量配置

在 `backend/server.py` 或 Docker 启动时可配置：

| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `MC_DEV_MODE` | `0` | 设为 `1` 开启开发模式，API 返回 Mock 数据，不加载模型（极速启动）。 |
| `MC_ENABLE_LONG_AUDIO` | `0` | 设为 `1` 允许 >20s 音频（以降级优先级处理）。设为 `0` 则直接拒绝长任务并返回 400。 |
| `HF_ENDPOINT` | `https://hf-mirror.com` | Hugging Face 镜像地址，国内服务器必须配置。 |

# 价值与展望

## 从“听觉”到“理解”：精准的提示词构建体系
不同于传统方法只依赖用户输入的简单关键词（如“生成一首摇滚”），本项目的创新在于让 AI 先“听懂”原曲。
*   **创新点**：我们构建了一套**音频特征翻译机制**。系统会首先对原曲进行深度扫描，提取出音域跨度、旋律走向、节奏强弱等关键特征。
*   **具体实现**：这些物理特征不会被直接丢弃，而是被动态“翻译”成自然语言描述（Prompt）。例如，当系统检测到原曲旋律起伏很大时，会自动生成“具有表现力的宽音域”这样的指令喂给生成模型。这意味着，**AI 不是在瞎编，而是在严格遵循原曲的骨架进行再创作**，从而保证了生成结果与原曲的神似。

## 自动化“质检员”与闭环迭代
目前市面上的生成式 AI 大多是“盲盒模式”，生成好坏全凭运气。本项目最大的贡献在于引入了一个**基于数据驱动的自动化评审系统**。
*   **核心机制**：我们利用项目前期收集整理的**数百首音乐样本**，构建了专属的风格与情绪识别模块（即系统内部的评分引擎）。这个模块就像一位严苛的“质检员”。
*   **工作流程**：
    1.  当 MusicGen 生成一段音乐后，“质检员”会立即介入，判断其风格是否偏离，情绪是否到位。
    2.  如果得分未达标，系统会自动判定为“失败”，并调整参数重新尝试，直到生成出高分结果。
    3.  这种**“生成-评分-修正”的闭环机制**，极大地提高了输出结果的稳定性，解决了 AI 生成质量忽高忽低的问题。

## 解决生成模型的“长音频崩坏”难题
开源的大模型（如 MusicGen）通常存在“短视”问题，一旦生成超过 30 秒的音乐，就容易出现静音、乱码或结构混乱。
*   **工程贡献**：我们设计了一套**分片重构与信号修复算法**。
    *   系统将长音乐切分为多个逻辑片段，分别进行风格迁移。
    *   在拼接时，引入了波形监测机制。一旦检测到某一段音频出现能量塌陷（音量突然变小或消失），算法会立即通过上下文进行信号修复。这使得本项目能够稳定处理全长歌曲，突破了原模型的长度限制。

## 与传统方法的对比

| 维度 | 纯传统算法 | 直接使用 AI 模型 | **本项目的混合架构** |
| :--- | :--- | :--- | :--- |
| **听感质量** | 机械、生硬，像电子合成音 | 逼真，但容易“跑题”，丢失原曲旋律 | **既逼真又还原**，保留原曲灵魂，重塑风格皮囊 |
| **可控性** | 非常高，但上限低 | 低，像抽奖一样不可控 | **高**，通过特征翻译和质检系统实现了精确控制 |
| **稳定性** | 稳定 | 不稳定，长音频容易崩坏 | **自适应**，通过工程手段修复了模型的原生缺陷 |

---

## 未来展望

*   **细粒度与结构化控制**：
    目前的系统主要依赖宏观的“情绪”和“风格”标签。未来计划引入更深维度的控制能力：
    *   **配器指定**：允许用户通过 Prompt 明确指定或排除特定乐器（如“加入失真吉他独奏”或“移除打击乐”）。
    *   **分轨编辑**：引入源分离技术，支持生成后对鼓、贝斯、人声、旋律等声部进行独立调整或替换。
    *   **动态密度调整**：增加对音乐织体密度（稀疏/密集）和节奏型的参数化控制。

*   **丰富交互维度**：引入更多模态的输入控制，例如支持通过文字描述与音频参考相结合的多模态 Prompt，让生成结果更精准。

*   **流式传输体验**：将目前的“全量生成后下载”升级为 WebSocket 流式传输，实现边生成边播放，大幅降低用户感知的等待时间。

---

# 第三方说明

本项目核心依赖于以下开源项目：

## 核心模型

-   **[YAMNet (TensorFlow Hub)](https://tfhub.dev/google/yamnet/1)**: 用于音频事件分类与特征提取。Apache 2.0 许可。
-   **[MusicGen (Meta AI)](https://huggingface.co/facebook/musicgen-small)**: 基于 Transformer 的高质量音乐生成模型。CC-BY-NC 4.0 许可。

## 基础框架

-   **[FastAPI](https://fastapi.tiangolo.com/)**: 高性能 Python Web 框架。
-   **[Librosa](https://librosa.org/)**: 音频信号处理标准库。
-   **[Hugging Face Transformers](https://huggingface.co/docs/transformers/index)**: 模型加载与管理。
>>>>>>> c874920e640810b96189f8502876ab84f4a50610

# 写在最后

这个项目由小组的五位成员共同完成。

<<<<<<< HEAD
@dieWehmut @spacewolf28 @NanXiang-git @lsw6132 @XiaoYang-Zhou
=======
@dieWehmut @spacewolf28 @NanXiang-git @lsw6132 @XiaoYang-Zhou
>>>>>>> c874920e640810b96189f8502876ab84f4a50610
