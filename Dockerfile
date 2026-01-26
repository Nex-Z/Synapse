# ============================================
# Synapse Docker 镜像 - 多阶段构建
# ============================================

# ---- 阶段 1: 前端构建 ----
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# 安装 pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# 复制依赖文件
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制前端源码
COPY frontend/ ./

# 构建前端 (使用空 API 路径用于同源部署)
ENV VITE_API_BASE_URL=""
RUN pnpm run build


# ---- 阶段 2: 后端运行环境 ----
FROM python:3.12-slim AS runtime

WORKDIR /app

# 安装 uv 包管理器
RUN pip install uv --no-cache-dir

# 复制后端依赖文件
COPY backend/pyproject.toml backend/uv.lock ./

# 安装 Python 依赖
RUN uv sync --frozen --no-dev

# 复制后端源码
COPY backend/ ./

# 从前端构建阶段复制静态文件
COPY --from=frontend-builder /app/frontend/dist ./static

# 创建数据目录
RUN mkdir -p /app/data

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 暴露端口
EXPOSE 8000

# 健康检查 (使用 Python 替代 curl)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')" || exit 1

# 启动命令
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
