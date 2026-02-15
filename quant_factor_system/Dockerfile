# QuantFactorSystem Docker镜像
FROM python:3.10-slim

LABEL maintainer="quant@system.com"
LABEL description="QuantFactorSystem - 量化因子分析系统"
LABEL version="3.0.0"

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制项目代码
COPY . .

# 创建必要目录
RUN mkdir -p /app/data /app/logs /app/cache

# 默认命令
CMD ["python", "cli.py", "info"]
