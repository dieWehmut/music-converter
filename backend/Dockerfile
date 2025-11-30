FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安装构建时需要的系统包（注意：这些会在同一 RUN 中移除以减少最终镜像体积）
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3-venv \
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

# 构建时可选择是否安装重量级依赖（torch/transformers/tensorflow）
ARG INSTALL_HEAVY=false
ARG INSTALL_INFERENCE=false

# 复制 requirements 与代码
COPY backend/requirements-light.txt /app/requirements-light.txt
COPY backend/requirements.txt /app/requirements.txt
COPY backend/requirements-inference.txt /app/requirements-inference.txt
COPY backend /app/backend

# 创建虚拟环境并安装 Python 依赖（使用 --prefer-binary 优先使用预编译 wheel）
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --prefer-binary --only-binary=:all: pip setuptools wheel \
    && if [ "$INSTALL_HEAVY" = "true" ] ; then \
        /opt/venv/bin/pip install --no-cache-dir --prefer-binary --only-binary=:all: -r /app/requirements.txt ; \
    elif [ "$INSTALL_INFERENCE" = "true" ] ; then \
        /opt/venv/bin/pip install --no-cache-dir --prefer-binary --only-binary=:all: -r /app/requirements-inference.txt ; \
    else \
        /opt/venv/bin/pip install --no-cache-dir --prefer-binary --only-binary=:all: -r /app/requirements-light.txt ; \
    fi \
    && /opt/venv/bin/pip install --no-cache-dir gunicorn \
    # 清理构建工具以减小镜像层（仅在 builder 阶段执行）
    && apt-get remove -y --purge build-essential python3-venv pkg-config gfortran \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


FROM python:3.10-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# 仅安装运行时所需的系统库（不包含构建工具）
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libsndfile1 \
        ca-certificates \
        libopenblas-dev \
        liblapack-dev \
        libblas-dev \
        libgomp1 \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 将虚拟环境和代码从 builder 复制到最终镜像
COPY --from=builder /opt/venv /opt/venv
COPY backend /app/backend

EXPOSE 8000

# 生产使用单 worker 避免重复加载大型模型
# 使用 Railway/容器平台提供的 PORT 环境变量，如果未提供则回退到 8000
CMD ["sh", "-c", "gunicorn backend.server:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --workers 1 --log-level info"]
