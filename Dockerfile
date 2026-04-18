FROM python:3.11-slim

WORKDIR /app

# 复制依赖文件
COPY pyproject.toml .

# 安装依赖
RUN pip install --no-cache-dir . && \
    pip install --no-cache-dir uvicorn

# 复制 src 目录
COPY src/ ./src/

# 设置 Python 路径，让 app 包可以被直接导入
ENV PYTHONPATH=/app/src

EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]