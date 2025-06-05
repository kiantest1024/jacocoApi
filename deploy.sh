#!/bin/bash

echo "🚀 JaCoCo Scanner API Docker部署脚本"
echo "=================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 设置变量
IMAGE_NAME="jacoco-scanner-api"
CONTAINER_NAME="jacoco-scanner-api"
PORT="8002"

echo "📋 部署配置:"
echo "  镜像名称: $IMAGE_NAME"
echo "  容器名称: $CONTAINER_NAME"
echo "  服务端口: $PORT"
echo ""

# 停止并删除现有容器
echo "🛑 停止现有服务..."
docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# 删除旧镜像
echo "🗑️ 清理旧镜像..."
docker rmi $IMAGE_NAME:latest 2>/dev/null || true

# 构建新镜像
echo "🔨 构建Docker镜像..."
if docker build -f Dockerfile.service -t $IMAGE_NAME:latest .; then
    echo "✅ 镜像构建成功"
else
    echo "❌ 镜像构建失败"
    exit 1
fi

# 启动服务
echo "🚀 启动服务..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
if curl -f http://localhost:$PORT/health &> /dev/null; then
    echo "✅ 服务启动成功！"
    echo ""
    echo "📡 服务信息:"
    echo "  API地址: http://localhost:$PORT"
    echo "  API文档: http://localhost:$PORT/docs"
    echo "  健康检查: http://localhost:$PORT/health"
    echo "  报告列表: http://localhost:$PORT/reports"
    echo ""
    echo "📊 容器状态:"
    docker ps | grep $CONTAINER_NAME
    echo ""
    echo "📝 查看日志: docker logs $CONTAINER_NAME"
    echo "🛑 停止服务: docker-compose down"
else
    echo "❌ 服务启动失败，检查日志:"
    docker logs $CONTAINER_NAME
    exit 1
fi
