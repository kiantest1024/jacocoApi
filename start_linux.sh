#!/bin/bash

# Linux 环境专用启动脚本
# 修复 Python 3.12+ 兼容性问题

set -e

echo "=========================================="
echo "GitHub Webhook JaCoCo API Linux 启动器"
echo "=========================================="

# 检查 Python 版本
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python 版本: $PYTHON_VERSION"

# 检查是否在正确的目录
if [ ! -f "main.py" ]; then
    echo "错误: 请在 jacocoApi 目录中运行此脚本"
    echo "当前目录: $(pwd)"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "升级 pip..."
pip install --upgrade pip

# 安装 setuptools（修复 distutils 问题）
echo "安装 setuptools..."
pip install setuptools>=65.0.0

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt

# 检查环境配置文件
if [ ! -f ".env" ]; then
    echo "创建环境配置文件..."
    cp .env.example .env
    echo
    echo "注意: 请编辑 .env 文件配置您的 GitHub webhook 密钥"
    echo
fi

# 检查 Redis 是否运行
echo "检查 Redis 连接..."
if python3 -c "import redis; r=redis.Redis(); r.ping(); print('Redis 连接正常')" 2>/dev/null; then
    echo "✓ Redis 连接正常"
    REDIS_AVAILABLE=true
else
    echo "⚠ 警告: Redis 连接失败"
    echo "Push 事件处理需要 Redis 支持"
    echo "您可以使用 Docker 启动 Redis: docker run -d -p 6379:6379 redis:alpine"
    REDIS_AVAILABLE=false
fi

# 检查 Docker
echo "检查 Docker..."
if command -v docker &> /dev/null; then
    echo "✓ Docker 可用"
    DOCKER_AVAILABLE=true
else
    echo "⚠ 警告: Docker 未安装"
    echo "JaCoCo 扫描需要 Docker 支持"
    DOCKER_AVAILABLE=false
fi

echo
echo "=========================================="
echo "启动服务"
echo "=========================================="

# 创建日志目录
mkdir -p logs

# 启动 Celery worker (如果 Redis 可用)
if [ "$REDIS_AVAILABLE" = true ]; then
    echo "启动 Celery worker..."
    celery -A jacoco_tasks.celery_app worker --loglevel=info --detach \
        --pidfile=logs/celery.pid --logfile=logs/celery.log
    
    # 等待一下让 Celery 启动
    sleep 3
    echo "✓ Celery worker 已启动"
else
    echo "⚠ 跳过 Celery worker 启动（Redis 不可用）"
fi

# 启动 FastAPI 服务器
echo "启动 FastAPI 服务器..."
echo
echo "服务将在以下地址启动:"
echo "  - API 服务: http://localhost:8001"
echo "  - API 文档: http://localhost:8001/docs"
echo "  - 健康检查: http://localhost:8001/health"
echo "  - GitHub Webhook: http://localhost:8001/github/webhook"
echo
echo "功能状态:"
echo "  - GitHub Webhook 接收: ✓ 可用"
echo "  - Ping 事件处理: ✓ 可用"
if [ "$REDIS_AVAILABLE" = true ]; then
    echo "  - Push 事件处理: ✓ 可用"
else
    echo "  - Push 事件处理: ⚠ 需要 Redis"
fi
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "  - JaCoCo 扫描: ✓ 可用"
else
    echo "  - JaCoCo 扫描: ⚠ 需要 Docker"
fi
echo
echo "按 Ctrl+C 停止服务"
echo

# 设置清理函数
cleanup() {
    echo
    echo "正在停止服务..."
    
    # 停止 Celery worker
    if [ -f "logs/celery.pid" ]; then
        echo "停止 Celery worker..."
        kill $(cat logs/celery.pid) 2>/dev/null || true
        rm -f logs/celery.pid
    fi
    
    echo "服务已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 启动 FastAPI 服务器
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# 如果到达这里，说明服务器正常退出
cleanup
