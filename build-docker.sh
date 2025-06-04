#!/bin/bash

# JaCoCo Scanner Docker镜像构建脚本

set -e

echo "🐳 构建JaCoCo Scanner Docker镜像..."

# 检查Docker是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装或不在PATH中"
    exit 1
fi

# 检查Docker守护进程是否运行
if ! docker info &> /dev/null; then
    echo "❌ Docker守护进程未运行"
    exit 1
fi

# 检查必要文件是否存在
if [[ ! -f "docker/Dockerfile" ]]; then
    echo "❌ 未找到Dockerfile: docker/Dockerfile"
    exit 1
fi

if [[ ! -d "docker/scripts" ]]; then
    echo "❌ 未找到脚本目录: docker/scripts"
    exit 1
fi

# 构建镜像
echo "📦 开始构建Docker镜像..."

# 检测网络环境并选择构建参数
if ping -c 1 deb.debian.org &> /dev/null; then
    echo "🌍 使用官方源构建..."
    BUILD_ARGS="--no-cache"
else
    echo "⚠️ 网络连接异常，尝试使用DNS配置..."
    BUILD_ARGS="--no-cache --dns=8.8.8.8 --dns=8.8.4.4"
fi

echo "🔧 构建参数: $BUILD_ARGS"

# 构建镜像
docker build $BUILD_ARGS -t jacoco-scanner:latest -f docker/Dockerfile docker/

if [[ $? -eq 0 ]]; then
    echo "✅ Docker镜像构建成功: jacoco-scanner:latest"
    
    # 显示镜像信息
    echo ""
    echo "📋 镜像信息:"
    docker images jacoco-scanner:latest
    
    echo ""
    echo "🎉 构建完成！现在可以使用Docker扫描模式了。"
    echo ""
    echo "💡 使用说明:"
    echo "   - 服务将优先使用Docker扫描"
    echo "   - 如果Docker不可用，会自动回退到本地扫描"
    echo "   - 可以通过配置强制使用本地扫描"
else
    echo "❌ Docker镜像构建失败"
    exit 1
fi
