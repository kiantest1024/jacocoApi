#!/bin/bash

# Ubuntu 简化启动脚本
# 专为 Ubuntu/Debian 系统优化

set -e

echo "========================================"
echo "Universal JaCoCo Scanner API - Ubuntu"
echo "========================================"
echo

# 检查 Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✓ Python3: $(python3 --version)"
else
    echo "❌ Python3 未找到，正在安装..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
    PYTHON_CMD="python3"
fi

# 检查 pip
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo "❌ pip 未找到，正在安装..."
    sudo apt install -y python3-pip
fi

# 检查当前目录
if [ ! -f "main.py" ]; then
    echo "❌ 请在 jacocoApi 目录中运行此脚本"
    echo "当前目录: $(pwd)"
    exit 1
fi

echo "✓ 当前目录正确: $(pwd)"

# 安装依赖（直接安装，不使用虚拟环境）
echo "📦 安装 Python 依赖..."
$PYTHON_CMD -m pip install --user -r requirements.txt

# 检查 Redis（可选）
echo "🔍 检查 Redis..."
if $PYTHON_CMD -c "import redis; r=redis.Redis(); r.ping(); print('Redis OK')" 2>/dev/null; then
    echo "✓ Redis 连接正常"
else
    echo "⚠ Redis 未运行，将跳过 Celery 功能"
    echo "如需完整功能，请安装 Redis:"
    echo "  sudo apt install redis-server"
    echo "  sudo systemctl start redis"
fi

# 检查 Docker（可选）
if command -v docker &> /dev/null; then
    echo "✓ Docker 可用"
else
    echo "⚠ Docker 未安装，JaCoCo 扫描功能将受限"
    echo "安装 Docker: sudo apt install docker.io"
fi

echo
echo "🚀 启动服务器..."
echo "📡 服务地址: http://localhost:8002"
echo "📖 API 文档: http://localhost:8002/docs"
echo "🔗 Webhook: http://localhost:8002/github/webhook-no-auth"
echo
echo "按 Ctrl+C 停止服务"
echo

# 启动服务器
$PYTHON_CMD -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload
