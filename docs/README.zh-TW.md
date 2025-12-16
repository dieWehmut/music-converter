<h1 style="text-align: center;">Music Converter</h1>

<div align="center">

[简体中文](../README.md) | **繁體中文** | [English](README.en.md) | [日本語](README.ja.md)

</div>

---

# 專案簡介

Music Converter 是一套端對端的音樂情緒／風格轉換實驗專案。使用者上傳支援的音訊（WAV、MP3 等），系統會先解析其風格與情緒特徵，再依據目標風格與情緒生成新的編曲。前端由 Vue 3 + Vite 驅動，後端使用 FastAPI，對接深度學習推論管線。

## 目錄

- [專案簡介](#專案簡介)
  - [目錄](#目錄)
  - [功能亮點](#功能亮點)
  - [架構概覽](#架構概覽)
    - [主要內容](#主要內容)
    - [目錄概覽](#目錄概覽)
  - [環境需求](#環境需求)
  - [本機測試](#本機測試)
    - [後端設定](#後端設定)
    - [前端設定](#前端設定)
    - [API 測試](#api-測試)
  - [部署說明](#部署說明)
    - [後端部署](#後端部署)
    - [前端部署](#前端部署)
  - [API 說明](#api-說明)
    - [非同步任務](#非同步任務)
    - [回應欄位](#回應欄位)
    - [環境變數](#環境變數)
  - [疑難排解](#疑難排解)
  - [第三方說明](#第三方說明)
    - [核心模型](#核心模型)
    - [基礎框架](#基礎框架)
- [寫在最後](#寫在最後)

## 功能亮點

- **多格式支援**：上傳 WAV/MP3（或任何 `librosa` 支援的格式）並可直接在瀏覽器中試聽。
- **智慧分析**：執行風格與情緒辨識模型（YAMNet + 自訂分類器），回傳機率分佈，方便視覺化與後續決策。
- **生成式轉換**：選擇目標風格／情緒後，觸發非同步音樂生成任務（基於 MusicGen），完成後可下載或播放結果。
- **持久化體驗**：前端使用 IndexedDB 快取上傳與任務狀態，重新整理頁面也不會遺失。
- **開發者友善**：`MC_DEV_MODE=1` 可啟用 DEV 模式，快速回傳偽造但穩定的資料，方便無 GPU 的前端聯調。

## 架構概覽

### 主要內容

- **前端**（`frontend/`）：核心頁面 `src/views/Home.vue`，負責上傳音訊、渲染任務進度、展示結果，並提供目標風格與情緒的選擇控件。
- **後端**（`backend/`）：`server.py` 提供 API、管理背景任務，並載入 `backend/inference/full_pipeline.py` 的 `FullMusicPipeline`，支援風格與情緒的分析與生成。
- **模型堆疊**：PyTorch (MusicGen)、TensorFlow (YAMNet)、Transformers、librosa 等依賴列於 `backend/requirements.txt`。

### 目錄概覽

```
music-converter/
├── backend/
│   ├── server.py — FastAPI 應用程式入口，定義路由、CORS、任務佇列與檔案輸出路徑
│   ├── requirements.txt — 後端 Python 依賴
│   ├── features/ — 音訊特徵提取相關程式碼目錄
│   │   └── yamnet_extract.py — 封裝 YAMNet，提供 Embedding 與類別機率提取
│   ├── inference/ — 推論與生成管線核心模組（分析 → Prompt → 生成 → 後處理）
│   │   ├── full_pipeline.py — `FullMusicPipeline`：協調分析、Prompt 建構與生成的高階類別
│   │   ├── generate_music.py — 與 MusicGen 互動，載入模型並儲存生成音訊
│   │   ├── analyze.py — 組合分析流程，呼叫特徵提取與分類器並組織輸出
│   │   ├── emotion_recognition.py — 情緒辨識封裝，回傳情緒標籤與信心度
│   │   ├── melody_extractor.py — 提取主旋律/音高序列的工具
│   │   ├── melody_scorer.py — 對旋律或生成結果做相似度/品質評分
│   │   ├── melody_transformer.py — 將旋律變換為目標風格的邏輯
│   │   ├── prompt_builder.py — 建構傳給 MusicGen 的 Prompt (提示詞)
│   │   └── style_recognition.py — 風格辨識封裝，回傳風格標籤及信心度
│   ├── models/ — 模型存放（可離線放置模型權重）
│   │   ├── yamnet/ — YAMNet 離線模型
│   │   └── ... 
│   └── utils/ — 各類輔助函式
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   └── Home.vue — 主頁面
│   │   ├── api/
│   │   │   ├── index.js — API 基礎客戶端，配置 `baseURL` 與統一請求封裝
│   │   │   ├── emotion.js — 封裝獲取情緒標籤的呼叫
│   │   │   └── upload.js — 封裝檔案上傳、啟動轉換與查詢任務狀態的 API
│   │   └── ...
│   └── ...
└── ...
```

## 環境需求

- **作業系統**：Windows / macOS / Linux (建議 Ubuntu 22.04)。
- **Node.js**：`^20.19.0` 或 `>=22.12.0`。
- **Python**：3.10 及以上（強烈建議使用 Conda 管理）。
- **硬體**：
  - **記憶體**：建議 **16GB** 以上（同時載入 TF 和 PyTorch 模型較耗記憶體）。
  - **GPU**：支援 CUDA 的 NVIDIA 顯示卡（8GB+ 視訊記憶體/顯存），以便秒級完成生成任務。純 CPU 亦可執行但較慢。
- **系統工具**：FFmpeg（必須安裝，用於音訊處理）。

## 本機測試

### 後端設定

請先準備好 Python 3.10+ 環境（建議使用 Conda）。

**第一步：進入目錄並建立環境**

```bash
cd backend

# [通用] 使用 Conda 建立環境
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

**第二步：安裝系統依賴 (僅 Linux)**

Windows 和 macOS 使用者通常不需要此步驟，除非缺少 FFmpeg。

```bash
# Ubuntu/Debian 範例
sudo apt update && sudo apt install -y ffmpeg git
```

**第三步：安裝 Python 依賴**

```bash
pip install -r requirements.txt
```

**第四步：啟動後端服務**

根據你的作業系統選擇對應的指令。

**Windows (CMD / PowerShell)**

```powershell
# [可選] 啟用 DEV 模式 (跳過模型載入，適合無 GPU 除錯)
set MC_DEV_MODE=1

# 啟動服務
uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```

**macOS / Linux**

```bash
# [可選] 啟用 DEV 模式 (跳過模型載入，適合無 GPU 除錯)
export MC_DEV_MODE=1

# 啟動服務
uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```

終端機出現 `INFO: Application startup complete.` 即代表後端就緒。

> **模型下載提示**：首次啟動會自動下載模型。若網路受限，請參考下文「環境變數」設定 `HF_ENDPOINT` 鏡像，或手動下載 YAMNet 模型。

### 前端設定

確保已安裝 Node.js (v20+)。

**第一步：安裝依賴**

```bash
cd frontend
npm install
```

**第二步：啟動開發伺服器**

```bash
npm run dev
```

預設訪問地址：`http://localhost:5173`。

### API 測試

本機除錯時，先確保後端已啟動並監聽 `http://localhost:8000`，再啟動前端並透過瀏覽器訪問 `http://localhost:5173` 進行互動測試。

- 瀏覽器測試：上傳音訊並觀察任務進度、情緒/風格預測與生成結果。

- 命令列（curl）範例：

1) 健康檢查
```bash
curl http://localhost:8000/health
```

2) 請求音訊特徵（分析）
```bash
curl -X POST -F "file=@/path/to/audio.wav" http://localhost:8000/api/features
```

3) 發起轉換任務（非同步）
```bash
curl -X POST -F "file=@/path/to/audio.wav" -F "style=pop" -F "emotion=happy" http://localhost:8000/api/convert
```

4) 查詢任務狀態
```bash
curl http://localhost:8000/api/tasks/01234567
```

## 部署說明

### 後端部署

在伺服器上長期執行時，建議配合 `nohup` 和 Nginx。

1. **啟動環境**：`source venv/bin/activate` 或 `conda activate mc-env`
2. **啟動服務 (背景執行)**：
   **注意**：請在專案根目錄（`music-converter`）下執行，以確保模組路徑正確。
   ```sh
   # 範例：背景啟動並將日誌輸出到 server.log
   nohup python3 -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
   ```
3. **Nginx 反向代理 (推薦)**：
   建議配置 Nginx 處理 HTTPS 及大檔案上傳限制。
   ```nginx
   server {
       listen 80;
       server_name api.your-domain.com;
       location / {
           proxy_pass http://127.0.0.1:8000;
           client_max_body_size 50M; # 允許大音訊檔案
       }
   }
   ```

### 前端部署

**方式 A：自動化部署 (推薦 - Vercel / Netlify / Railway)**
1. 將程式碼推送至 GitHub/GitLab。
2. 在 Vercel 或 Netlify 等平台匯入本專案。
3. **關鍵設定**：在部署平台的 **Environment Variables** (環境變數) 設定中，請務必修改/新增 API Base URL 設定，使其指向你的生產環境後端 HTTPS 地址（例如 `https://api.your-domain.com`）。

**方式 B：手動建構 (Nginx 靜態託管)**
```sh
cd frontend
npm run build
# 建構產物位於 frontend/dist
```
建構完成後，可將 `dist` 目錄內的檔案上傳至 Nginx 的靜態資源目錄 (`/var/www/html`) 或其他靜態託管服務。

## API 說明

| 方法 | 路徑 | 功能 |
|------|------|------|
| `GET` | `/` | 回傳簡單 HTML，確認後端在線 |
| `GET` | `/health` | 健康檢查，回傳 `ok` |
| `GET` | `/api/styles` | 回傳可用風格標籤 |
| `GET` | `/api/emotions` | 回傳可用情緒標籤 |
| `POST` | `/api/features` | 上傳音訊 `file`，回傳風格/情緒預測及機率 |
| `POST` | `/api/convert` | 上傳音訊並指定目標風格/情緒，啟動非同步轉換 |
| `GET` | `/api/tasks/{task_id}` | 查詢任務狀態（`pending`/`processing`/`success`/`failed`） |
| `GET` | `/api/tasks/{task_id}/download` | 任務成功後下載生成的 WAV |

### 非同步任務

1. 前端呼叫 `/api/convert` 上傳音訊。
2. 後端將任務寫入記憶體 `TASKS`，背景執行緒呼叫 `FullMusicPipeline.process`。
3. 前端輪詢 `/api/tasks/{task_id}`。
4. 狀態變為 `success` 時，呼叫下載介面獲取結果檔案。

### 回應欄位

- `task_id`: 內部任務 ID，用於查詢狀態與下載。
- `status`: `pending` / `processing` / `success` / `failed`。
- `message`: 可選的錯誤或進度訊息。
- `result.file`: 下載連結（若 `status === success`）。

### 環境變數
- `MC_DEV_MODE`: 設定為 `1` 時啟用 DEV 模式，回傳偽造數據並跳過模型載入。
- `HF_ENDPOINT`: 指定 Hugging Face 鏡像地址用於模型下載。
- `ALLOW_ORIGINS`: 可指定前端允許的 CORS 網域列表（在 `server.py` 中解析）。
- `PORT`: 服務連接埠（預設 8000）。

## 疑難排解

- **下載模型報錯 `Connection refused` / `Network unreachable`**：
  伺服器無法連線 Hugging Face 或 TFHub。請設定 `HF_ENDPOINT` 環境變數，或手動下載 YAMNet 模型至 `backend/models/yamnet/` 目錄。
- **啟動時顯示 `Killed`**：
  記憶體不足 (OOM)。請檢查 Swap 是否開啟，或升級伺服器記憶體。
- **`No module named backend.server`**：
  執行路徑錯誤。請退回到專案根目錄，使用 `python3 -m uvicorn backend.server:app` 啟動。
- **前端 CORS 錯誤**：
  檢查前端網域是否已新增到 `server.py` 的 `allow_origins` 列表。
- **Mixed Content 錯誤**：
  前端是 HTTPS，後端是 HTTP。請配置 Nginx + SSL 憑證，使後端支援 HTTPS。
- **上傳失敗 / 413 Payload Too Large**：
  Nginx 或前端上傳設定可能限制了檔案大小。請檢查 Nginx 的 `client_max_body_size` 和前端的上傳限制。
- **權限/路徑錯誤**：
  `backend/output` 目錄需要有寫入權限（執行使用者）。若發生權限錯誤，改變目錄權限或修改 `server.py` 中的輸出路徑。

## 第三方說明

本專案核心依賴於以下深度學習模型與框架。若打算分發本專案或其中的模型權重，請務必查看上游專案的授權條款（LICENSE）並在發布中包含必要的 LICENSE/NOTICE 檔案。

### 核心模型

- **YAMNet (TensorFlow Hub)**
  - **用途**：音訊事件分類與特徵提取。本專案使用 YAMNet 提取音訊的 Embeddings 特徵，用於後續的情緒與風格分析。
  - **來源**：[TensorFlow Hub - YAMNet](https://tfhub.dev/google/yamnet/1)
  - **授權**：Apache 2.0
  - **說明**：專案中如需離線使用，請將模型放置於 [backend/models/yamnet/](backend/models/yamnet/)（目錄下應包含 `saved_model.pb`、`variables/`、`assets/yamnet_class_map.csv` 等檔案）。

- **MusicGen (Meta AI / Hugging Face)**
  - **用途**：基於文字提示或音訊提示生成高品質音樂。本專案利用 MusicGen 根據使用者選擇的目標情緒與風格生成新的編曲。
  - **來源**：[Hugging Face - Facebook/MusicGen](https://huggingface.co/facebook/musicgen-small) (預設為 small 版本，可配置)
  - **授權**：CC-BY-NC 4.0 (非商業用途) / MIT (視具體模型版本而定，請務必核實)
  - **說明**：模型權重通常由 `transformers` 庫自動下載並快取。

### 基礎框架

- **TensorFlow / tensorflow-hub**：用於載入與執行 YAMNet 模型。
- **PyTorch**：用於執行 MusicGen 生成模型。
- **Hugging Face Transformers**：提供 MusicGen 的載入介面與預訓練權重管理。
- **Librosa**：用於音訊訊號處理、載入與特徵預處理。
- **FFmpeg**：底層音訊編解碼支援（系統級依賴）。

# 寫在最後

這個專案由小組的五位成員共同完成。

@dieWehmut @spacewolf28 @NanXiang-git @lsw6132 @XiaoYang-Zhou
```