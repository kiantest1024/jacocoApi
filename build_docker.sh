#!/bin/bash

echo "🐳 构建JaCoCo Docker镜像..."

if ! docker --version &> /dev/null; then
    echo "❌ Docker不可用"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker守护进程未运行"
    exit 1
fi

docker build -t jacoco-scanner:latest .

if [ $? -eq 0 ]; then
    echo "✅ 构建成功"
    docker images jacoco-scanner:latest
else
    echo "❌ 构建失败"
    exit 1
fi
