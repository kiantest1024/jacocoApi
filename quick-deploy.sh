#!/bin/bash

echo "⚡ JaCoCo Scanner API 快速部署"
echo "============================="

if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装"
    exit 1
fi

echo "🛑 清理现有容器..."
docker stop jacoco-scanner-api 2>/dev/null || true
docker rm jacoco-scanner-api 2>/dev/null || true

echo "🔨 构建Docker镜像..."
docker build -f Dockerfile.service -t jacoco-scanner-api:latest .

echo "🚀 启动容器..."
docker run -d \
  --name jacoco-scanner-api \
  -p 8002:8002 \
  -v $(pwd)/reports:/app/reports \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --restart unless-stopped \
  jacoco-scanner-api:latest

# 检查部署结果
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 快速部署成功！"
    echo ""
    echo "📡 服务信息:"
    echo "  API地址: http://localhost:8002"
    echo "  API文档: http://localhost:8002/docs"
    echo "  健康检查: http://localhost:8002/health"
    echo ""
    echo "🔧 管理命令:"
    echo "  查看日志: docker logs jacoco-scanner-api"
    echo "  停止服务: docker stop jacoco-scanner-api"
    echo "  删除容器: docker rm jacoco-scanner-api"
    echo "  重启服务: docker restart jacoco-scanner-api"
else
    echo "❌ 快速部署失败"
    exit 1
fi
