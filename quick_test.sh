#!/bin/bash

echo "🚀 快速Docker测试"

# 重建镜像
echo "🔨 重建Docker镜像..."
docker rmi jacoco-scanner:latest 2>/dev/null || true
docker build -t jacoco-scanner:latest .

if [ $? -ne 0 ]; then
    echo "❌ 镜像构建失败"
    exit 1
fi

echo "✅ 镜像构建成功"

# 测试镜像启动
echo "🧪 测试镜像启动..."
docker run --rm jacoco-scanner:latest

echo "✅ 测试完成"
