<h1 style="text-align: center;">Music Converter</h1>

<div align="center">

[简体中文](../README.md) | [繁體中文](README.zh-TW.md) | **English** | [日本語](README.ja.md)

</div>

---

# Project Overview

Music Converter is an end-to-end experimental project for music emotion and style transfer. Users can upload supported audio files (WAV, MP3, etc.), and the system analyzes their style and emotional characteristics before generating a new arrangement based on the target style and emotion. The frontend is powered by Vue 3 + Vite, while the backend utilizes FastAPI to interface with a deep learning inference pipeline.

## Table of Contents

- [Project Overview](#project-overview)
  - [Table of Contents](#table-of-contents)
  - [Key Features](#key-features)
  - [Architecture Overview](#architecture-overview)
    - [Core Components](#core-components)
    - [Directory Structure](#directory-structure)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
    - [Backend Setup](#backend-setup)
    - [Frontend Setup](#frontend-setup)
    - [API Testing](#api-testing)
  - [Deployment Guide](#deployment-guide)
    - [Backend Deployment](#backend-deployment)
    - [Frontend Deployment](#frontend-deployment)
  - [API Documentation](#api-documentation)
    - [Asynchronous Workflow](#asynchronous-workflow)
    - [Response Schema](#response-schema)
    - [Environment Variables](#environment-variables)
  - [Troubleshooting](#troubleshooting)
  - [Third-Party Notices](#third-party-notices)
    - [Core Models](#core-models)
    - [Infrastructure](#infrastructure)
- [Acknowledgements](#acknowledgements)

## Key Features

- **Multi-Format Support**: Upload WAV/MP3 files (or any format supported by `librosa`) with direct in-browser playback.
- **Intelligent Analysis**: Deploys style and emotion recognition models (YAMNet + Custom Classifiers) to return probability distributions, facilitating visualization and decision-making.
- **Generative Conversion**: Triggers asynchronous music generation tasks (based on MusicGen) upon selecting target styles/emotions. Results can be downloaded or played upon completion.
- **Persistent Experience**: Utilizes IndexedDB to cache uploads and task states, ensuring data persistence across page refreshes.
- **Developer Friendly**: `MC_DEV_MODE=1` enables a DEV mode that returns stable mock data, allowing frontend debugging without requiring a GPU.

## Architecture Overview

### Core Components

- **Frontend** (`frontend/`): The core interface is `src/views/Home.vue`, responsible for audio uploading, rendering task progress, displaying results, and providing controls for target style/emotion selection.
- **Backend** (`backend/`): `server.py` provides the API, manages background tasks, and initializes the `FullMusicPipeline` from `backend/inference/full_pipeline.py` to support analysis and generation.
- **Model Stack**: Dependencies such as PyTorch (MusicGen), TensorFlow (YAMNet), Transformers, and librosa are listed in `backend/requirements.txt`.

### Directory Structure

```
music-converter/
├── backend/
│   ├── server.py — FastAPI entry point; defines routes, CORS, task queues, and file output paths.
│   ├── requirements.txt — Python backend dependencies.
│   ├── features/ — Audio feature extraction modules.
│   │   └── yamnet_extract.py — Encapsulates YAMNet for embedding and class probability extraction.
│   ├── inference/ — Core inference and generation pipeline.
│   │   ├── full_pipeline.py — `FullMusicPipeline`: High-level class orchestrating analysis, prompt building, and generation.
│   │   ├── generate_music.py — Interacts with MusicGen to load models and save generated audio.
│   │   ├── analyze.py — Combines feature extraction and classifiers to structure analysis output.
│   │   ├── emotion_recognition.py — Emotion recognition wrapper returning labels and confidence scores.
│   │   ├── melody_extractor.py — Utilities for extracting main melody/pitch sequences.
│   │   ├── melody_scorer.py — Scoring logic for melody similarity or generation quality.
│   │   ├── melody_transformer.py — Logic for transforming melody into the target style.
│   │   ├── prompt_builder.py — Constructs prompts for MusicGen.
│   │   └── style_recognition.py — Style recognition wrapper returning labels and confidence scores.
│   ├── models/ — Directory for offline model weights.
│   │   ├── yamnet/ — Offline YAMNet model.
│   │   └── ... 
│   └── utils/ — Helper functions.
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   └── Home.vue — Main application view.
│   │   ├── api/
│   │   │   ├── index.js — Base API client with `baseURL` configuration and interceptors.
│   │   │   ├── emotion.js — API wrapper for fetching emotion labels.
│   │   │   └── upload.js — API wrapper for file uploads, conversion triggers, and status polling.
│   │   └── ...
│   └── ...
└── ...
```

## Prerequisites

- **Operating System**: Windows / macOS / Linux (Ubuntu 22.04 recommended).
- **Node.js**: `^20.19.0` or `>=22.12.0`.
- **Python**: 3.10 or higher (Conda is highly recommended).
- **Hardware**:
  - **RAM**: **16GB** or more recommended (loading both TF and PyTorch models is memory-intensive).
  - **GPU**: NVIDIA GPU with CUDA support (8GB+ VRAM) is recommended for second-level generation times. CPU execution is supported but significantly slower.
- **System Tools**: FFmpeg (Mandatory for audio processing).

## Local Development

### Backend Setup

Prepare a Python 3.10+ environment first (Conda recommended).

**Step 1: Create Environment**

```bash
cd backend

# [General] Create environment using Conda
conda create -n mc-env python=3.10 -y
conda activate mc-env
```

**Alternative: Using `venv`**

Windows:
```powershell
python -m venv venv
venv\Scripts\activate
```
macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

**Step 2: Install System Dependencies (Linux Only)**

Windows and macOS users usually do not need this step unless FFmpeg is missing.

```bash
# Ubuntu/Debian example
sudo apt update && sudo apt install -y ffmpeg git
```

**Step 3: Install Python Dependencies**

```bash
pip install -r requirements.txt
```

**Step 4: Start Backend Service**

Choose the command corresponding to your operating system.

**Windows (CMD / PowerShell)**

```powershell
# [Optional] Enable DEV mode (skips model loading, suitable for non-GPU debugging)
set MC_DEV_MODE=1

# Start service
uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```

**macOS / Linux**

```bash
# [Optional] Enable DEV mode (skips model loading, suitable for non-GPU debugging)
export MC_DEV_MODE=1

# Start service
uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```

When `INFO: Application startup complete.` appears in the terminal, the backend is ready.

> **Note on Models**: Models are downloaded automatically on first launch. If network access is restricted, set the `HF_ENDPOINT` environment variable (see below) or manually download the YAMNet model.

### Frontend Setup

Ensure Node.js (v20+) is installed.

**Step 1: Install Dependencies**

```bash
cd frontend
npm install
```

**Step 2: Start Development Server**

```bash
npm run dev
```

Default access URL: `http://localhost:5173`.

### API Testing

For local debugging, ensure the backend is listening on `http://localhost:8000`, then access the frontend at `http://localhost:5173`.

- **Browser Testing**: Upload audio to observe the progress bar, emotion/style predictions, and generation results.
- **Command Line (curl) Examples**:

1) Health Check
```bash
curl http://localhost:8000/health
```

2) Request Audio Features (Analysis)
```bash
curl -X POST -F "file=@/path/to/audio.wav" http://localhost:8000/api/features
```

3) Initiate Conversion Task (Async)
```bash
curl -X POST -F "file=@/path/to/audio.wav" -F "style=pop" -F "emotion=happy" http://localhost:8000/api/convert
```

4) Query Task Status
```bash
curl http://localhost:8000/api/tasks/01234567
```

## Deployment Guide

### Backend Deployment

For long-running server instances, usage of `nohup` and Nginx is recommended.

1. **Activate Environment**: `source venv/bin/activate` or `conda activate mc-env`
2. **Start Service (Background)**:
   **Note**: Run this from the project root (`music-converter`) to ensure correct module paths.
   ```sh
   # Example: Start in background and redirect logs to server.log
   nohup python3 -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
   ```
3. **Nginx Reverse Proxy (Recommended)**:
   Configure Nginx to handle HTTPS and increase file upload limits.
   ```nginx
   server {
       listen 80;
       server_name api.your-domain.com;
       location / {
           proxy_pass http://127.0.0.1:8000;
           client_max_body_size 50M; # Allow larger audio files
       }
   }
   ```

### Frontend Deployment

**Method A: Automated Deployment (Recommended - Vercel / Netlify / Railway)**
1. Push code to GitHub/GitLab.
2. Import the project into Vercel or Netlify.
3. **Critical Configuration**: In the deployment platform's **Environment Variables**, ensure you modify/add the API Base URL configuration to point to your production backend HTTPS address (e.g., `https://api.your-domain.com`).

**Method B: Manual Build (Nginx Static Hosting)**
```sh
cd frontend
npm run build
# Build artifacts are located in frontend/dist
```
Upload the contents of `dist` to your Nginx static resource directory (`/var/www/html`) or other static hosting services.

## API Documentation

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Returns simple HTML to confirm backend is online. |
| `GET` | `/health` | Health check, returns `ok`. |
| `GET` | `/api/styles` | Returns available style labels. |
| `GET` | `/api/emotions` | Returns available emotion labels. |
| `POST` | `/api/features` | Uploads audio `file`, returns style/emotion predictions and probabilities. |
| `POST` | `/api/convert` | Uploads audio and specifies target style/emotion to start async conversion. |
| `GET` | `/api/tasks/{task_id}` | Queries task status (`pending`/`processing`/`success`/`failed`). |
| `GET` | `/api/tasks/{task_id}/download` | Downloads the generated WAV file upon task success. |

### Asynchronous Workflow

1. Frontend calls `/api/convert` to upload audio.
2. Backend writes the task to the in-memory `TASKS` dictionary; a background thread calls `FullMusicPipeline.process`.
3. Frontend polls `/api/tasks/{task_id}`.
4. When status becomes `success`, the download endpoint is called to retrieve the result.

### Response Schema

- `task_id`: Internal task ID used for status queries and downloads.
- `status`: `pending` / `processing` / `success` / `failed`.
- `message`: Optional error or progress message.
- `result.file`: Download link (if `status === success`).

### Environment Variables
- `MC_DEV_MODE`: Set to `1` to enable DEV mode (returns mock data and skips model loading).
- `HF_ENDPOINT`: Specifies the Hugging Face mirror address for model downloads.
- `ALLOW_ORIGINS`: Specifies the list of allowed CORS domains for the frontend (parsed in `server.py`).
- `PORT`: Service port (default 8000).

## Troubleshooting

- **Model Download Error (`Connection refused` / `Network unreachable`)**:
  The server cannot connect to Hugging Face or TFHub. Set the `HF_ENDPOINT` environment variable or manually download the YAMNet model to `backend/models/yamnet/`.
- **Process Killed (`Killed`)**:
  Insufficient memory (OOM). Check if Swap is enabled or upgrade server RAM.
- **`No module named backend.server`**:
  Incorrect execution path. Return to the project root directory and start using `python3 -m uvicorn backend.server:app`.
- **Frontend CORS Error**:
  Check if the frontend domain is added to the `allow_origins` list in `server.py`.
- **Mixed Content Error**:
  Frontend is HTTPS, but Backend is HTTP. Configure Nginx + SSL certificates to enable HTTPS for the backend.
- **Upload Failed / 413 Payload Too Large**:
  Nginx or frontend upload configurations may be limiting file size. Check `client_max_body_size` in Nginx and frontend upload limits.
- **Permission/Path Errors**:
  The `backend/output` directory requires write permissions for the process user. If permission errors occur, modify directory permissions or the output path in `server.py`.

## Third-Party Notices

This project relies on the following deep learning models and frameworks. If you plan to distribute this project or its model weights, please ensure compliance with upstream licenses and include necessary LICENSE/NOTICE files.

### Core Models

- **YAMNet (TensorFlow Hub)**
  - **Usage**: Audio event classification and feature extraction. Used here to extract audio embeddings for emotion and style analysis.
  - **Source**: [TensorFlow Hub - YAMNet](https://tfhub.dev/google/yamnet/1)
  - **License**: Apache 2.0
  - **Note**: For offline use, place the model in [backend/models/yamnet/](backend/models/yamnet/) (directory should contain `saved_model.pb`, `variables/`, `assets/yamnet_class_map.csv`, etc.).

- **MusicGen (Meta AI / Hugging Face)**
  - **Usage**: High-quality music generation based on text or audio prompts. Used to generate new arrangements based on target emotion and style.
  - **Source**: [Hugging Face - Facebook/MusicGen](https://huggingface.co/facebook/musicgen-small) (Small version default, configurable).
  - **License**: CC-BY-NC 4.0 (Non-commercial) / MIT (Subject to specific model version; please verify).
  - **Note**: Model weights are typically downloaded and cached automatically by the `transformers` library.

### Infrastructure

- **TensorFlow / tensorflow-hub**: Loading and running the YAMNet model.
- **PyTorch**: Running the MusicGen generation model.
- **Hugging Face Transformers**: Interface for loading MusicGen and managing pre-trained weights.
- **Librosa**: Audio signal processing, loading, and feature preprocessing.
- **FFmpeg**: Underlying audio codec support (System-level dependency).

# Acknowledgements

This project was collaboratively completed by a team of five members:

@dieWehmut @spacewolf28 @NanXiang-git @lsw6132 @XiaoYang-Zhou
```