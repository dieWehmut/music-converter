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

# 构建时可选择是否安装重量级依赖（torch/tensorflow）
# 默认不安装以保持镜像小（使用 Railway 免费层时适合）。
# 若需要完整模型，在构建时传入 --build-arg INSTALL_HEAVY=true
ARG INSTALL_HEAVY=false

# 先把两个 requirements 都复制进来（small / full），再根据 build-arg 安装
COPY backend/requirements-light.txt /app/requirements-light.txt
COPY backend/requirements.txt /app/requirements.txt
COPY backend/ /app

RUN python -m pip install --upgrade pip
# 默认安装精简依赖，除非显式要求安装重量级依赖
RUN if [ "$INSTALL_HEAVY" = "true" ] ; then pip install --no-cache-dir -r requirements.txt ; else pip install --no-cache-dir -r requirements-light.txt ; fi
# 确保 gunicorn 可用（再次安装无害，且保证 runtime 有 gunicorn）
RUN pip install --no-cache-dir gunicorn

EXPOSE 8000

# 生产使用单 worker 避免重复加载大型模型
# 使用 Railway/容器平台提供的 PORT 环境变量，如果未提供则回退到 8000
CMD ["sh", "-c", "gunicorn server:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --workers 1 --log-level info"]
