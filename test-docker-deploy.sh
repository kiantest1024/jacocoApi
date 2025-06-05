#!/bin/bash

echo "🧪 测试Docker部署"
echo "=================="

# 检查Docker是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装"
    exit 1
fi

echo "✅ Docker已安装"

# 测试构建服务镜像
echo "🔨 测试构建API服务镜像..."
if docker build -f Dockerfile.service -t jacoco-scanner-api:test .; then
    echo "✅ Debian基础API服务镜像构建成功"
elif docker build -f Dockerfile.ubuntu -t jacoco-scanner-api:test .; then
    echo "✅ Ubuntu基础API服务镜像构建成功"
else
    echo "❌ API服务镜像构建失败"
    exit 1
fi

# 测试构建扫描镜像
echo "🔨 测试构建扫描镜像..."
if docker build -t jacoco-scanner:test .; then
    echo "✅ 扫描镜像构建成功"
else
    echo "❌ 扫描镜像构建失败"
    exit 1
fi

# 清理测试镜像
echo "🗑️ 清理测试镜像..."
docker rmi jacoco-scanner-api:test jacoco-scanner:test 2>/dev/null || true

echo "✅ Docker部署测试完成"
echo ""
echo "🚀 可以使用以下命令进行部署:"
echo "  快速部署: ./quick-deploy.sh"
echo "  完整部署: ./deploy.sh"
echo "  Compose部署: docker-compose up -d"
