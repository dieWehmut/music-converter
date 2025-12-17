# 使用官方 Python 3.9 精简版镜像
FROM python:3.9-slim

# 设置工作目录为 /app
WORKDIR /app

# 设置环境变量
# 防止 Python 生成 pyc 文件
ENV PYTHONDONTWRITEBYTECODE=1
# 防止 Python 缓冲 stdout/stderr，确保日志实时输出
ENV PYTHONUNBUFFERED=1
# 设置 HuggingFace 镜像源 (可选，构建时可覆盖)
ENV HF_ENDPOINT=https://hf-mirror.com

# 1. 安装系统级依赖
# libsndfile1: soundfile 库必须
# ffmpeg: librosa 处理 mp3 等音频必须
# git: 有些 pip 包可能需要从 git 安装
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. 复制依赖文件并安装
# 假设 Dockerfile 在项目根目录，backend/requirements.txt 在下级
COPY backend/requirements.txt /app/backend/requirements.txt

# 升级 pip 并安装依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# 3. 复制源代码
# 将本地的 backend 文件夹复制到容器的 /app/backend
COPY backend /app/backend

# 4. 暴露端口
EXPOSE 8000

# 5. 启动命令
# 这里的运行目录是 /app，所以 python -m backend.server 是合法的
CMD ["python", "-m", "backend.server"]