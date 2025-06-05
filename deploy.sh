#!/bin/bash

echo "🚀 JaCoCo Scanner API Docker部署"
echo "==============================="

if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose未安装"
    exit 1
fi

IMAGE_NAME="jacoco-scanner-api"
CONTAINER_NAME="jacoco-scanner-api"

echo "🛑 停止现有服务..."
docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

echo "🔨 构建Docker镜像..."
docker build -f Dockerfile.service -t $IMAGE_NAME:latest .

echo "🚀 启动服务..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

echo "⏳ 等待服务启动..."
sleep 10

echo "🔍 检查服务状态..."
if curl -f http://localhost:8002/health &> /dev/null; then
    echo "✅ 服务启动成功！"
    echo "📡 API地址: http://localhost:8002"
    echo "📖 API文档: http://localhost:8002/docs"
else
    echo "❌ 服务启动失败"
    docker logs $CONTAINER_NAME
    exit 1
fi
