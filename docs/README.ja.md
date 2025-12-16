<h1 style="text-align: center;">Music Converter</h1>

<div align="center">

[简体中文](../README.md) | [繁體中文](README.zh-TW.md) | [English](README.en.md) | **日本語**

</div>

---

# プロジェクト概要

Music Converter は、エンドツーエンドの音楽感情・スタイル変換実験プロジェクトです。ユーザーがサポートされている形式のオーディオ（WAV、MP3 等）をアップロードすると、システムはまずそのスタイルと感情の特徴を解析し、ターゲットとなるスタイルと感情に基づいて新しい楽曲（編曲）を生成します。フロントエンドは Vue 3 + Vite で駆動し、バックエンドは FastAPI を使用してディープラーニング推論パイプラインと連携します。

## 目次

- [プロジェクト概要](#プロジェクト概要)
  - [目次](#目次)
  - [主な機能](#主な機能)
  - [アーキテクチャ概観](#アーキテクチャ概観)
    - [主要コンポーネント](#主要コンポーネント)
    - [ディレクトリ構成](#ディレクトリ構成)
  - [動作環境](#動作環境)
  - [ローカルでのテスト](#ローカルでのテスト)
    - [バックエンド設定](#バックエンド設定)
    - [フロントエンド設定](#フロントエンド設定)
    - [API テスト](#api-テスト)
  - [デプロイ手順](#デプロイ手順)
    - [バックエンドのデプロイ](#バックエンドのデプロイ)
    - [フロントエンドのデプロイ](#フロントエンドのデプロイ)
  - [API 仕様](#api-仕様)
    - [非同期タスク](#非同期タスク)
    - [レスポンスフィールド](#レスポンスフィールド)
    - [環境変数](#環境変数)
  - [トラブルシューティング](#トラブルシューティング)
  - [サードパーティに関する表示](#サードパーティに関する表示)
    - [コアモデル](#コアモデル)
    - [基礎フレームワーク](#基礎フレームワーク)
- [謝辞](#謝辞)

## 主な機能

- **多様なフォーマット対応**: WAV/MP3（または `librosa` がサポートする任意の形式）をアップロードし、ブラウザで直接プレビュー再生が可能。
- **インテリジェント分析**: スタイルおよび感情認識モデル（YAMNet + カスタム分類器）を実行し、確率分布を返すことで、可視化や意思決定を支援。
- **生成 AI による変換**: 目標とするスタイル/感情を選択後、非同期の音楽生成タスク（MusicGen ベース）をトリガー。完了後に結果をダウンロードまたは再生可能。
- **データの永続化**: フロントエンドでは IndexedDB を使用してアップロード内容やタスク状態をキャッシュするため、ページをリロードしてもデータが失われません。
- **開発者フレンドリー**: `MC_DEV_MODE=1` を設定することで DEV モードが有効になり、GPU なしでのフロントエンド連携用に、偽造された安定したデータを即座に返します。

## アーキテクチャ概観

### 主要コンポーネント

- **フロントエンド** (`frontend/`): コアとなる `src/views/Home.vue` は、オーディオのアップロード、タスク進捗のレンダリング、結果の表示、およびターゲットスタイル/感情の選択コントロールを提供します。
- **バックエンド** (`backend/`): `server.py` が API を提供し、バックグラウンドタスクを管理します。また、`backend/inference/full_pipeline.py` の `FullMusicPipeline` をロードし、スタイル・感情の分析と生成をサポートします。
- **モデルスタック**: PyTorch (MusicGen)、TensorFlow (YAMNet)、Transformers、librosa 等の依存関係は `backend/requirements.txt` に記載されています。

### ディレクトリ構成

```
music-converter/
├── backend/
│   ├── server.py — FastAPI アプリのエントリポイント。ルーティング、CORS、タスクキュー、ファイル出力パスを定義
│   ├── requirements.txt — バックエンドの Python 依存パッケージ
│   ├── features/ — 音声特徴抽出関連のコード
│   │   └── yamnet_extract.py — YAMNet をカプセル化し、Embedding とクラス確率を抽出
│   ├── inference/ — 推論および生成パイプラインのコアモジュール
│   │   ├── full_pipeline.py — `FullMusicPipeline`：分析、プロンプト構築、生成を調整する高レベルクラス
│   │   ├── generate_music.py — MusicGen と対話し、モデルのロードと生成音声の保存を行う
│   │   ├── analyze.py — 特徴抽出と分類器を組み合わせて分析フローを構成
│   │   ├── emotion_recognition.py — 感情認識ラッパー。感情ラベルと信頼度スコアを返す
│   │   ├── melody_extractor.py — メロディ/ピッチシーケンス抽出ツール
│   │   ├── melody_scorer.py — メロディや生成結果の類似度/品質スコアリング
│   │   ├── melody_transformer.py — メロディをターゲットスタイルへ変換するロジック
│   │   ├── prompt_builder.py — MusicGen に渡すプロンプトを構築
│   │   └── style_recognition.py — スタイル認識ラッパー。スタイルラベルと信頼度スコアを返す
│   ├── models/ — モデル格納場所（オフラインモデル用）
│   │   ├── yamnet/ — YAMNet オフラインモデル
│   │   └── ... 
│   └── utils/ — 各種ヘルパー関数
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   └── Home.vue — メインページ
│   │   ├── api/
│   │   │   ├── index.js — API 基底クライアント。`baseURL` 設定とリクエストの共通化
│   │   │   ├── emotion.js — 感情ラベル取得 API のカプセル化
│   │   │   └── upload.js — ファイルアップロード、変換トリガー、タスク状態確認 API のカプセル化
│   │   └── ...
│   └── ...
└── ...
```

## 動作環境

- **OS**: Windows / macOS / Linux (Ubuntu 22.04 推奨)。
- **Node.js**: `^20.19.0` または `>=22.12.0`。
- **Python**: 3.10 以上（Conda による管理を強く推奨）。
- **ハードウェア**:
  - **メモリ**: **16GB** 以上推奨（TF と PyTorch モデルを同時にロードするためメモリを消費します）。
  - **GPU**: CUDA 対応の NVIDIA グラフィックカード（VRAM 8GB 以上）。秒単位で生成タスクを完了するために推奨されます。CPU のみでも動作しますが、速度は大幅に低下します。
- **システムツール**: FFmpeg（必須。音声処理に使用）。

## ローカルでのテスト

### バックエンド設定

まず Python 3.10+ 環境を準備してください（Conda 推奨）。

**ステップ 1: 環境の作成**

```bash
cd backend

# [汎用] Conda を使用して環境を作成
conda create -n mc-env python=3.10 -y
conda activate mc-env
```

**`venv` を使用する場合**

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

**ステップ 2: システム依存関係のインストール (Linux のみ)**

Windows および macOS ユーザーは、FFmpeg が不足していない限り通常このステップは不要です。

```bash
# Ubuntu/Debian の例
sudo apt update && sudo apt install -y ffmpeg git
```

**ステップ 3: Python 依存関係のインストール**

```bash
pip install -r requirements.txt
```

**ステップ 4: バックエンドサービスの起動**

OS に応じて以下のコマンドを実行してください。

**Windows (CMD / PowerShell)**

```powershell
# [オプション] DEV モードを有効化 (モデルロードをスキップ、GPU なしでのデバッグに最適)
set MC_DEV_MODE=1

# サービスの起動
uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```

**macOS / Linux**

```bash
# [オプション] DEV モードを有効化 (モデルロードをスキップ、GPU なしでのデバッグに最適)
export MC_DEV_MODE=1

# サービスの起動
uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```

ターミナルに `INFO: Application startup complete.` と表示されればバックエンドの準備は完了です。

> **モデルのダウンロードについて**: 初回起動時にモデルが自動的にダウンロードされます。ネットワーク制限がある場合は、後述の「環境変数」で `HF_ENDPOINT` ミラーを設定するか、手動で YAMNet モデルをダウンロードしてください。

### フロントエンド設定

Node.js (v20+) がインストールされていることを確認してください。

**ステップ 1: 依存関係のインストール**

```bash
cd frontend
npm install
```

**ステップ 2: 開発サーバーの起動**

```bash
npm run dev
```

デフォルトのアクセス先: `http://localhost:5173`。

### API テスト

ローカルデバッグ時は、バックエンドが `http://localhost:8000` で待機していることを確認してから、フロントエンド `http://localhost:5173` にブラウザでアクセスして対話テストを行ってください。

- ブラウザテスト: 音声をアップロードし、タスクの進捗バー、感情/スタイルの予測、生成結果を確認します。

- コマンドライン (curl) の例:

1) ヘルスチェック
```bash
curl http://localhost:8000/health
```

2) 音声特徴のリクエスト（分析）
```bash
curl -X POST -F "file=@/path/to/audio.wav" http://localhost:8000/api/features
```

3) 変換タスクの開始（非同期）
```bash
curl -X POST -F "file=@/path/to/audio.wav" -F "style=pop" -F "emotion=happy" http://localhost:8000/api/convert
```

4) タスク状態の照会
```bash
curl http://localhost:8000/api/tasks/01234567
```

## デプロイ手順

### バックエンドのデプロイ

サーバーで長時間実行する場合は、`nohup` と Nginx の併用を推奨します。

1. **環境のアクティベート**: `source venv/bin/activate` または `conda activate mc-env`
2. **サービスの起動 (バックグラウンド)**:
   **注意**: モジュールパスを正しく認識させるため、必ずプロジェクトルート (`music-converter`) で実行してください。
   ```sh
   # 例: バックグラウンドで起動し、ログを server.log に出力
   nohup python3 -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
   ```
3. **Nginx リバースプロキシ (推奨)**:
   HTTPS 化および大容量ファイルアップロード制限の緩和のために Nginx を設定します。
   ```nginx
   server {
       listen 80;
       server_name api.your-domain.com;
       location / {
           proxy_pass http://127.0.0.1:8000;
           client_max_body_size 50M; # 大きな音声ファイルを許可
       }
   }
   ```

### フロントエンドのデプロイ

**方法 A: 自動デプロイ (推奨 - Vercel / Netlify / Railway)**
1. コードを GitHub/GitLab にプッシュします。
2. Vercel や Netlify 等のプラットフォームで本プロジェクトをインポートします。
3. **重要な設定**: デプロイプラットフォームの **Environment Variables** (環境変数) 設定にて、API Base URL が本番環境のバックエンド HTTPS アドレス（例: `https://api.your-domain.com`）を指すように修正/追加してください。

**方法 B: 手動ビルド (Nginx 静的ホスティング)**
```sh
cd frontend
npm run build
# ビルド成果物は frontend/dist に生成されます
```
ビルド完了後、`dist` ディレクトリ内のファイルを Nginx の静的リソースディレクトリ (`/var/www/html`) やその他の静的ホスティングサービスにアップロードします。

## API 仕様

| メソッド | パス | 機能 |
|------|------|------|
| `GET` | `/` | バックエンドのオンライン確認用簡易 HTML を返す |
| `GET` | `/health` | ヘルスチェック、`ok` を返す |
| `GET` | `/api/styles` | 利用可能なスタイルラベルを返す |
| `GET` | `/api/emotions` | 利用可能な感情ラベルを返す |
| `POST` | `/api/features` | 音声 `file` をアップロードし、スタイル/感情の予測と確率を返す |
| `POST` | `/api/convert` | 音声をアップロードし、ターゲットのスタイル/感情を指定して非同期変換を開始 |
| `GET` | `/api/tasks/{task_id}` | タスク状態を照会 (`pending`/`processing`/`success`/`failed`) |
| `GET` | `/api/tasks/{task_id}/download` | タスク成功後、生成された WAV ファイルをダウンロード |

### 非同期タスク

1. フロントエンドが `/api/convert` を呼び出し、音声をアップロード。
2. バックエンドがタスクをメモリ上の `TASKS` に書き込み、バックグラウンドスレッドで `FullMusicPipeline.process` を実行。
3. フロントエンドが `/api/tasks/{task_id}` をポーリング。
4. ステータスが `success` になると、ダウンロード API を呼び出して結果ファイルを取得。

### レスポンスフィールド

- `task_id`: 状態照会やダウンロードに使用する内部タスク ID。
- `status`: `pending` / `processing` / `success` / `failed`。
- `message`: オプションのエラーまたは進捗メッセージ。
- `result.file`: ダウンロードリンク（`status === success` の場合）。

### 環境変数
- `MC_DEV_MODE`: `1` に設定すると DEV モードが有効になり、モデルロードをスキップしてダミーデータを返します。
- `HF_ENDPOINT`: モデルダウンロード用の Hugging Face ミラーアドレスを指定します。
- `ALLOW_ORIGINS`: フロントエンドの許可する CORS ドメインリストを指定します（`server.py` 内で解析）。
- `PORT`: サービスポート（デフォルト 8000）。

## トラブルシューティング

- **モデルダウンロードエラー `Connection refused` / `Network unreachable`**:
  サーバーが Hugging Face または TFHub に接続できていません。`HF_ENDPOINT` 環境変数を設定するか、YAMNet モデルを手動で `backend/models/yamnet/` に配置してください。
- **起動時に `Killed` と表示される**:
  メモリ不足 (OOM) です。Swap が有効か確認するか、サーバーのメモリを増設してください。
- **`No module named backend.server`**:
  実行パスが誤っています。プロジェクトルートディレクトリに戻り、`python3 -m uvicorn backend.server:app` で起動してください。
- **フロントエンドの CORS エラー**:
  フロントエンドのドメインが `server.py` の `allow_origins` リストに追加されているか確認してください。
- **Mixed Content エラー**:
  フロントエンドが HTTPS でバックエンドが HTTP の場合に発生します。Nginx + SSL 証明書を設定し、バックエンドを HTTPS 化してください。
- **アップロード失敗 / 413 Payload Too Large**:
  Nginx またはフロントエンドのアップロード設定がファイルサイズを制限している可能性があります。Nginx の `client_max_body_size` とフロントエンドの制限を確認してください。
- **権限/パスのエラー**:
  `backend/output` ディレクトリに書き込み権限が必要です。権限エラーが発生する場合は、ディレクトリの権限を変更するか、`server.py` で出力パスを変更してください。

## サードパーティに関する表示

本プロジェクトは以下のディープラーニングモデルおよびフレームワークに依存しています。本プロジェクトまたはモデルの重みを再配布する場合は、必ずアップストリームプロジェクトのライセンス（LICENSE）を確認し、必要な LICENSE/NOTICE ファイルを含めてください。

### コアモデル

- **YAMNet (TensorFlow Hub)**
  - **用途**: 音響イベント分類および特徴抽出。本プロジェクトでは YAMNet を使用して音声の Embedding 特徴を抽出し、感情およびスタイル分析に利用しています。
  - **出典**: [TensorFlow Hub - YAMNet](https://tfhub.dev/google/yamnet/1)
  - **ライセンス**: Apache 2.0
  - **注記**: オフラインで使用する場合は、[backend/models/yamnet/](backend/models/yamnet/) にモデルを配置してください（ディレクトリには `saved_model.pb`、`variables/`、`assets/yamnet_class_map.csv` 等が含まれている必要があります）。

- **MusicGen (Meta AI / Hugging Face)**
  - **用途**: テキストまたは音声プロンプトに基づく高品質な音楽生成。本プロジェクトでは、MusicGen を利用して、ユーザーが選択したターゲット感情とスタイルに基づき新しい編曲を生成します。
  - **出典**: [Hugging Face - Facebook/MusicGen](https://huggingface.co/facebook/musicgen-small) (デフォルトは small 版、設定可能)
  - **ライセンス**: CC-BY-NC 4.0 (非商用利用) / MIT (具体的なモデルバージョンによるため、必ず確認してください)
  - **注記**: モデルの重みは通常 `transformers` ライブラリによって自動的にダウンロードおよびキャッシュされます。

### 基礎フレームワーク

- **TensorFlow / tensorflow-hub**: YAMNet モデルのロードと実行に使用。
- **PyTorch**: MusicGen 生成モデルの実行に使用。
- **Hugging Face Transformers**: MusicGen のロードインターフェースおよび事前学習済み重みの管理を提供。
- **Librosa**: 音声信号処理、ロード、特徴の前処理に使用。
- **FFmpeg**: 低レイヤーでの音声コーデックサポート（システム依存）。

# 謝辞

このプロジェクトは、以下の5名のメンバーによるグループワークによって完成しました。

@dieWehmut @spacewolf28 @NanXiang-git @lsw6132 @XiaoYang-Zhou
```