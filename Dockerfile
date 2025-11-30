FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖（libsndfile 用于 soundfile/librosa）
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libsndfile1 \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
## 复制整个构建上下文到镜像 /app
# 支持两种构建场景：
# 1) 构建上下文为仓库根（此时子模块通常不会被展开到父仓库），
#    /app/backend 可能不存在（因为 submodule 内容不在父仓库中）。
# 2) 构建上下文为 backend（若 CI/你配置了 Root Directory=backend），
#    此时 /app 就是后端代码根目录。
# 我们先复制上下文，然后按存在的 requirements 路径安装依赖。
COPY . /app

# 安装 pip 并根据位置选择 requirements.txt
RUN python -m pip install --upgrade pip
RUN if [ -f /app/backend/requirements.txt ]; then pip install -r /app/backend/requirements.txt; elif [ -f /app/requirements.txt ]; then pip install -r /app/requirements.txt; else echo "requirements.txt not found"; exit 1; fi
RUN pip install gunicorn

EXPOSE 8000

# 生产使用单 worker 避免重复加载大型模型
CMD ["gunicorn", "backend.server:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "1", "--log-level", "info"]
