#!/bin/bash

# 构建JaCoCo扫描器Docker镜像

echo "========================================"
echo "构建 JaCoCo Scanner Docker 镜像"
echo "========================================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    echo "Ubuntu: sudo apt install docker.io"
    exit 1
fi

echo "✓ Docker 可用: $(docker --version)"

# 检查当前目录
if [ ! -f "docker/Dockerfile.jacoco-scanner" ]; then
    echo "❌ 请在 jacocoApi 目录中运行此脚本"
    echo "当前目录: $(pwd)"
    exit 1
fi

echo "✓ 当前目录正确"

# 检查必要文件
echo "🔍 检查必要文件..."

if [ ! -f "maven-configs/jacoco-pom-overlay.xml" ]; then
    echo "❌ 缺少 Maven 配置文件"
    exit 1
fi

if [ ! -f "docker/scripts/scan.sh" ]; then
    echo "❌ 缺少扫描脚本"
    exit 1
fi

echo "✓ 所有必要文件存在"

# 构建镜像
echo
echo "🔨 开始构建 Docker 镜像..."
echo "镜像名称: jacoco-scanner:latest"
echo

# 使用Dockerfile构建
docker build -f docker/Dockerfile.jacoco-scanner -t jacoco-scanner:latest .

if [ $? -eq 0 ]; then
    echo
    echo "✅ Docker 镜像构建成功！"
    echo
    echo "📋 镜像信息:"
    docker images jacoco-scanner:latest
    echo
    echo "🧪 测试镜像:"
    echo "docker run --rm jacoco-scanner:latest echo 'Hello from JaCoCo Scanner'"
    echo
    echo "🚀 现在可以使用 JaCoCo 扫描功能了！"
else
    echo
    echo "❌ Docker 镜像构建失败"
    echo "请检查错误信息并重试"
    exit 1
fi
