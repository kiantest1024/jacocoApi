#!/bin/bash

echo "🧪 简单Docker测试"

# 检查Docker是否可用
if ! docker --version > /dev/null 2>&1; then
    echo "❌ Docker不可用"
    exit 1
fi

echo "✅ Docker可用"

# 检查镜像是否存在
if ! docker images -q jacoco-scanner:latest | grep -q .; then
    echo "❌ JaCoCo镜像不存在，开始构建..."
    docker build -t jacoco-scanner:latest .
    if [ $? -ne 0 ]; then
        echo "❌ 镜像构建失败"
        exit 1
    fi
fi

echo "✅ JaCoCo镜像存在"

# 测试镜像启动
echo "🧪 测试镜像启动..."
docker run --rm jacoco-scanner:latest --help

if [ $? -eq 0 ]; then
    echo "✅ Docker镜像测试成功"
else
    echo "❌ Docker镜像测试失败"
    echo "🔄 尝试重建镜像..."
    docker rmi jacoco-scanner:latest
    docker build --no-cache -t jacoco-scanner:latest .
    
    if [ $? -eq 0 ]; then
        echo "✅ 镜像重建成功"
        docker run --rm jacoco-scanner:latest --help
    else
        echo "❌ 镜像重建失败"
        exit 1
    fi
fi

echo "🎉 Docker测试完成"
