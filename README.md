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

<!-- 第二行：Python、MusicGen Model 和 License -->
<div>
<a href="https://www.python.org/">
  <img src="https://img.shields.io/badge/PYTHON-3.9+-blue?style=flat-square&logo=python&logoColor=white&labelColor=555555" alt="Python Version">
</a>
<a href="https://huggingface.co/facebook/musicgen-small" target="_blank">
  <img src="https://img.shields.io/badge/MODEL-MusicGen-FFD21E?style=flat-square&logo=huggingface&logoColor=white&labelColor=555555" alt="Hugging Face Model">
</a>
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

- **1.技术门槛高**：借助 YAMNet 模型的音频特征提取能力（通过 `backend/features/yamnet_extract.py` 封装实现）和 MusicGen 的音乐生成能力，让非专业用户无需掌握音乐理论即可完成风格转换。

- **2.处理效率低**：通过 `backend/inference/full_pipeline.py` 中的 `FullMusicPipeline` 类实现分析 - 生成全流程自动化，将传统需要数小时的编曲工作缩短至分钟级。

- **3.效果不稳定**：引入 `backend/inference/evaluate_generated.py` 中的评估体系，从风格增益、情绪增益、原始风格脱离度等多维度量化转换效果，确保输出质量。

系统融合前端交互（核心界面 、后端 API 服务与深度学习推理 pipeline，既实现了对音频处理与生成技术的工程化落地，也为音乐创意表达提供了新的技术范式。

# 功能亮点

- **多格式支持**：上传 WAV/MP3（或任何 `librosa` 支持的格式）并直接在浏览器中试听。
- **智能分析**：运行风格与情绪识别模型（YAMNet + 自定义分类器），返回概率分布，方便可视化与后续决策。
- **生成式转换**：选择目标风格/情绪后，触发异步音乐生成任务（基于 MusicGen），完成后可下载或播放结果。
- **智能队列系统**：后端内置优先级队列，短任务（<20s）自动插队优先处理，长任务后台排队。
- **长音频支持**：通过自动化切片与拼接技术，突破 MusicGen 的 30s 生成限制，支持任意长度音频。
- **持久化体验**：前端使用 IndexedDB 缓存上传与任务状态，刷新页面也不会丢失。

# 技术实现

## 主要内容

- **前端**（`frontend/`）：核心界面 `src/views/Home.vue`，负责上传音频、渲染任务进度、展示结果，并提供目标风格与情绪的选择控件。
- **后端**（`backend/`）：`server.py` 提供 API、管理后台任务，并加载 `backend/inference/full_pipeline.py` 的 `FullMusicPipeline`，支持风格与情绪的分析与生成。
- **模型栈**：PyTorch (MusicGen)、TensorFlow (YAMNet)、Transformers、librosa 等依赖列于 `backend/requirements.txt`。

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

# 本地开发指南

## 后端设置

请先准备好 Python 3.10+ 环境（推荐使用 Conda）。

**步骤 1：创建并激活环境**

```bash
cd backend
conda create -n mc-env python=3.10 -y
conda activate mc-env
```
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

```bash
pip install -r requirements.txt
```
> **预期输出**：显示 `Successfully installed torch... tensorflow...` 等信息，无红色报错。

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

```bash
cd frontend
npm install
```

**步骤 2：启动开发服务器**

```bash
npm run dev
```
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
    3.  这种“生成-评分-修正”的闭环机制，极大地提高了输出结果的稳定性，解决了 AI 生成质量忽高忽低的问题。

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

# 写在最后

这个项目由小组的五位成员共同完成。

@dieWehmut @spacewolf28 @NanXiang-git @lsw6132 @XiaoYang-Zhou