#!/bin/bash

echo "🐳 构建JaCoCo Docker镜像..."

# 检查Docker是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装或不可用"
    exit 1
fi

# 构建镜像
docker build -t jacoco-scanner:latest .

if [ $? -eq 0 ]; then
    echo "✅ JaCoCo Docker镜像构建成功"
    echo "📋 镜像信息:"
    docker images jacoco-scanner:latest
else
    echo "❌ JaCoCo Docker镜像构建失败"
    exit 1
fi
