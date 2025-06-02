#!/bin/bash

# Docker 镜像构建脚本
# 构建 JaCoCo 扫描器 Docker 镜像

set -e

# 配置
IMAGE_NAME="jacoco-scanner"
IMAGE_TAG="latest"
DOCKERFILE_PATH="docker/Dockerfile.jacoco-scanner"

echo "=========================================="
echo "构建 JaCoCo 扫描器 Docker 镜像"
echo "=========================================="
echo "镜像名称: $IMAGE_NAME:$IMAGE_TAG"
echo "Dockerfile: $DOCKERFILE_PATH"
echo "=========================================="

# 检查 Docker 是否可用
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装或不在 PATH 中"
    exit 1
fi

# 检查 Dockerfile 是否存在
if [[ ! -f "$DOCKERFILE_PATH" ]]; then
    echo "错误: Dockerfile 不存在: $DOCKERFILE_PATH"
    exit 1
fi

# 检查必要的文件和目录
echo "检查必要的文件..."

REQUIRED_FILES=(
    "maven-configs/jacoco-pom-overlay.xml"
    "docker/scripts/scan.sh"
    "docker/scripts/generate-enhanced-pom.sh"
    "docker/scripts/generate-summary.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "错误: 必需文件不存在: $file"
        exit 1
    fi
    echo "✓ $file"
done

# 设置脚本执行权限
echo "设置脚本执行权限..."
chmod +x docker/scripts/*.sh

# 构建 Docker 镜像
echo "开始构建 Docker 镜像..."
docker build -t "$IMAGE_NAME:$IMAGE_TAG" -f "$DOCKERFILE_PATH" .

if [[ $? -eq 0 ]]; then
    echo "✓ Docker 镜像构建成功: $IMAGE_NAME:$IMAGE_TAG"
else
    echo "✗ Docker 镜像构建失败"
    exit 1
fi

# 显示镜像信息
echo "=========================================="
echo "镜像信息:"
docker images "$IMAGE_NAME:$IMAGE_TAG"

echo "=========================================="
echo "构建完成!"
echo "=========================================="
echo "使用方法:"
echo "  docker run --rm -v \$(pwd)/reports:/app/reports \\"
echo "    $IMAGE_NAME:$IMAGE_TAG \\"
echo "    --repo-url https://github.com/user/repo.git \\"
echo "    --commit-id abc123 \\"
echo "    --branch main"
echo "=========================================="
