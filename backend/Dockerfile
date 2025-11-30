FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖（libsndfile 用于 soundfile/librosa）。
# 增加数值/并行库和运行时库，减少 TensorFlow/NumPy/BLAS 相关的缺失问题。
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libsndfile1 \
        git \
        ca-certificates \
        libopenblas-dev \
        liblapack-dev \
        libblas-dev \
        gfortran \
        libgomp1 \
        pkg-config \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制 requirements 再复制代码以利用缓存层
COPY backend/requirements.txt /app/requirements.txt
COPY backend/ /app

RUN python -m pip install --upgrade pip
# requirements.txt 中可包含 PyTorch CPU wheel 源 (-f)
# 使用 --no-cache-dir 降低镜像大小并避免缓存相关问题
RUN pip install --no-cache-dir -r requirements.txt
# 确保 gunicorn 可用
RUN pip install gunicorn

EXPOSE 8000

# 生产使用单 worker 避免重复加载大型模型
# 使用 Railway/容器平台提供的 PORT 环境变量，如果未提供则回退到 8000
CMD ["sh", "-c", "gunicorn server:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --workers 1 --log-level info"]
