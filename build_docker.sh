#!/bin/bash

echo "🐳 构建JaCoCo Docker镜像..."

# 检查Docker是否可用
if ! docker --version &> /dev/null; then
    echo "❌ Docker未安装或不可用"
    exit 1
fi

# 检查Docker守护进程是否运行
if ! docker info &> /dev/null; then
    echo "❌ Docker守护进程未运行"
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
