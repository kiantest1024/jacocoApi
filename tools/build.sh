#!/bin/bash
# JaCoCo Scanner 构建工具

set -e

echo "🚀 构建 JaCoCo Scanner"
echo "===================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker 服务未运行"
    exit 1
fi

# 设置脚本权限
chmod +x docker/scripts/*.sh

# 构建镜像
echo "🔨 构建镜像..."
docker build -f docker/Dockerfile.alpine -t jacoco-scanner:latest docker/

echo "✅ 构建完成"
docker images | grep jacoco-scanner
