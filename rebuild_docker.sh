#!/bin/bash

echo "🔄 重建JaCoCo Docker镜像..."

# 删除旧镜像
echo "🗑️ 删除旧镜像..."
docker rmi jacoco-scanner:latest 2>/dev/null || echo "旧镜像不存在，跳过删除"

# 清理Docker缓存
echo "🧹 清理Docker缓存..."
docker system prune -f

# 重新构建镜像
echo "🔨 重新构建镜像..."
docker build --no-cache -t jacoco-scanner:latest .

if [ $? -eq 0 ]; then
    echo "✅ JaCoCo Docker镜像重建成功"
    echo "📋 镜像信息:"
    docker images jacoco-scanner:latest
    
    echo ""
    echo "🧪 测试镜像..."
    docker run --rm jacoco-scanner:latest --help || echo "镜像测试完成"
else
    echo "❌ JaCoCo Docker镜像重建失败"
    exit 1
fi
