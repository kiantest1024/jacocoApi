#!/bin/bash

# 重新构建Docker镜像以修复扫描问题
echo "🔧 重新构建JaCoCo Scanner Docker镜像..."

# 删除旧镜像
echo "🗑️ 删除旧镜像..."
docker rmi jacoco-scanner:latest 2>/dev/null || true

# 构建新镜像
echo "📦 构建新镜像..."
docker build --no-cache -t jacoco-scanner:latest -f docker/Dockerfile docker/

if [ $? -eq 0 ]; then
    echo "✅ Docker镜像构建成功"
    
    # 显示镜像信息
    echo "📊 镜像信息:"
    docker images jacoco-scanner:latest
    
    echo ""
    echo "🎉 修复完成！主要改进："
    echo "1. ✅ 修复了MaxPermSize参数问题（改为MetaspaceSize）"
    echo "2. ✅ 添加了Maven依赖解析优化"
    echo "3. ✅ 配置了Maven镜像仓库"
    echo "4. ✅ 增强了错误处理和回退机制"
    echo ""
    echo "💡 现在可以重新测试扫描功能"
else
    echo "❌ Docker镜像构建失败"
    exit 1
fi
