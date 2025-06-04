#!/bin/bash

# 完整启动脚本 - 同时启动API服务和Celery Worker

echo "========================================"
echo "Universal JaCoCo Scanner - 完整启动"
echo "========================================"

# 检查Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python 未安装"
    exit 1
fi

echo "✓ Python: $($PYTHON_CMD --version)"

# 检查当前目录
if [ ! -f "main.py" ]; then
    echo "❌ 请在 jacocoApi 目录中运行此脚本"
    exit 1
fi

# 检查Redis
echo "🔍 检查Redis..."
if $PYTHON_CMD -c "import redis; r=redis.Redis(); r.ping(); print('Redis OK')" 2>/dev/null; then
    echo "✅ Redis 连接正常"
    USE_CELERY=true
else
    echo "⚠️ Redis 未运行，将使用同步模式"
    echo "如需异步模式，请启动Redis: sudo systemctl start redis-server"
    USE_CELERY=false
fi

# 创建日志目录
mkdir -p logs

# 清理函数
cleanup() {
    echo
    echo "🛑 正在停止服务..."
    
    # 停止Celery worker
    if [ -f "logs/celery.pid" ]; then
        echo "停止 Celery worker..."
        kill $(cat logs/celery.pid) 2>/dev/null || true
        rm -f logs/celery.pid
    fi
    
    # 停止API服务
    if [ ! -z "$API_PID" ]; then
        echo "停止 API 服务..."
        kill $API_PID 2>/dev/null || true
    fi
    
    echo "✅ 服务已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

echo
echo "🚀 启动服务..."

if [ "$USE_CELERY" = true ]; then
    # 启动Celery Worker (后台)
    echo "📋 启动 Celery worker..."
    $PYTHON_CMD -m celery -A jacoco_tasks.celery_app worker --loglevel=info --detach \
        --pidfile=logs/celery.pid --logfile=logs/celery.log
    
    if [ $? -eq 0 ]; then
        echo "✅ Celery worker 已启动"
    else
        echo "❌ Celery worker 启动失败，切换到同步模式"
        USE_CELERY=false
    fi
    
    # 等待Celery启动
    sleep 3
fi

echo
echo "📡 启动 API 服务..."
echo "🌐 服务地址: http://localhost:8002"
echo "📖 API 文档: http://localhost:8002/docs"
echo "🔗 Webhook: http://localhost:8002/github/webhook-no-auth"
echo

if [ "$USE_CELERY" = true ]; then
    echo "🔄 模式: 异步处理 (Celery + Redis)"
else
    echo "⚡ 模式: 同步处理 (直接执行)"
fi

echo
echo "按 Ctrl+C 停止所有服务"
echo

# 启动API服务
$PYTHON_CMD app.py &
API_PID=$!

# 等待API服务启动
sleep 2

# 检查API服务是否启动成功
if kill -0 $API_PID 2>/dev/null; then
    echo "✅ API 服务已启动 (PID: $API_PID)"
else
    echo "❌ API 服务启动失败"
    cleanup
    exit 1
fi

# 保持脚本运行
wait $API_PID
