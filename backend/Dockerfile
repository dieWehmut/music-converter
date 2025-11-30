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

# 先复制 requirements 再复制代码以利用缓存层
COPY requirements.txt /app/requirements.txt
COPY . /app

RUN python -m pip install --upgrade pip
# requirements.txt 中可包含 PyTorch CPU wheel 源 (-f)
RUN pip install -r requirements.txt
# 确保 gunicorn 可用
RUN pip install gunicorn

EXPOSE 8000

# 生产使用单 worker 避免重复加载大型模型
CMD ["gunicorn", "server:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "1", "--log-level", "info"]
