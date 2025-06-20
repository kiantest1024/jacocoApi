#!/bin/bash

# JaCoCo Scanner Docker镜像构建脚本 (Linux版本)
set -e

echo "🚀 开始构建 JaCoCo Scanner Docker 镜像..."

# 检查Docker是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装或不可用"
    echo "💡 Linux 安装命令:"
    echo "   Ubuntu/Debian: sudo apt install docker.io"
    echo "   CentOS/RHEL: sudo yum install docker"
    exit 1
fi

# 检查Docker服务是否运行
if ! docker info &> /dev/null; then
    echo "❌ Docker 服务未运行"
    echo "💡 启动 Docker 服务:"
    echo "   sudo systemctl start docker"
    echo "   sudo systemctl enable docker"
    exit 1
fi

# 进入项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 当前目录: $(pwd)"

# 检查必要文件
if [[ ! -f "docker/Dockerfile.alpine" ]]; then
    echo "❌ 未找到 docker/Dockerfile.alpine"
    exit 1
fi

if [[ ! -f "docker/scripts/scan.sh" ]]; then
    echo "❌ 未找到 docker/scripts/scan.sh"
    exit 1
fi

# 构建镜像
echo "🔨 构建 jacoco-scanner:latest 镜像..."
docker build -f docker/Dockerfile.alpine -t jacoco-scanner:latest docker/

# 检查构建结果
if docker images | grep -q "jacoco-scanner.*latest"; then
    echo "✅ JaCoCo Scanner 镜像构建成功！"
    echo ""
    echo "📋 镜像信息:"
    docker images | grep jacoco-scanner
    echo ""
    echo "🧪 测试镜像:"
    echo "docker run --rm jacoco-scanner:latest --help"
else
    echo "❌ 镜像构建失败"
    exit 1
fi

echo ""
echo "🎉 构建完成！现在可以使用 JaCoCo API 进行 Docker 扫描了。"
echo ""
echo "💡 下一步："
echo "   1. 运行诊断: python3 diagnose.py"
echo "   2. 测试扫描: docker run --rm jacoco-scanner:latest --help"
echo "   3. 启动 API: python3 app.py"
