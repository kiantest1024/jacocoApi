#!/bin/bash

# GitHub Webhook JaCoCo API 快速启动脚本 (Linux/Mac)
# 用于快速启动 GitHub webhook 接收服务

set -e

echo "========================================"
echo "GitHub Webhook JaCoCo API 快速启动"
echo "========================================"
echo

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装或不在 PATH 中"
    echo "请安装 Python 3.8+ 并确保在 PATH 中"
    exit 1
fi

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
else
    echo "⚠ 警告: Redis 连接失败"
    echo "请确保 Redis 服务正在运行"
    echo "您可以使用 Docker 启动 Redis: docker run -d -p 6379:6379 redis:alpine"
    echo
fi

# 检查 Java 和 Maven
echo "检查 Java 和 Maven..."
if command -v java &> /dev/null; then
    echo "✓ Java 可用: $(java -version 2>&1 | head -n 1)"
else
    echo "⚠ 警告: Java 未安装或不在 PATH 中"
    echo "JaCoCo 扫描需要 Java 11+"
fi

if command -v mvn &> /dev/null; then
    echo "✓ Maven 可用: $(mvn -version 2>&1 | head -n 1)"
else
    echo "⚠ 警告: Maven 未安装或不在 PATH 中"
    echo "JaCoCo 扫描需要 Maven 3.6+"
fi

echo
echo "========================================"
echo "启动服务"
echo "========================================"
echo

# 创建日志目录
mkdir -p logs

# 启动 Celery worker (后台)
echo "启动 Celery worker..."
celery -A jacoco_tasks.celery_app worker --loglevel=info --detach \
    --pidfile=logs/celery.pid --logfile=logs/celery.log

# 等待一下让 Celery 启动
sleep 3

# 启动 FastAPI 服务器
echo "启动 FastAPI 服务器..."
echo
echo "服务将在以下地址启动:"
echo "  - API 服务: http://localhost:8002"
echo "  - API 文档: http://localhost:8002/docs"
echo "  - 健康检查: http://localhost:8002/health"
echo "  - GitHub Webhook: http://localhost:8002/github/webhook"
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
python3 -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# 如果到达这里，说明服务器正常退出
cleanup
