#!/bin/bash

echo "🔍 验证Docker部署配置"
echo "====================="

# 检查必要文件
echo "📋 检查必要文件..."
files=(
    "Dockerfile.service"
    "Dockerfile.ubuntu" 
    "docker-compose.yml"
    "deploy.sh"
    "quick-deploy.sh"
    "app.py"
    "requirements.txt"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file 缺失"
    fi
done

# 检查Docker是否可用
echo ""
echo "🐳 检查Docker环境..."
if command -v docker &> /dev/null; then
    echo "✅ Docker已安装"
    docker --version
    
    if docker info &> /dev/null; then
        echo "✅ Docker服务运行正常"
    else
        echo "⚠️ Docker服务未运行或权限不足"
    fi
else
    echo "❌ Docker未安装"
fi

# 检查脚本权限
echo ""
echo "🔐 检查脚本权限..."
scripts=("deploy.sh" "quick-deploy.sh" "test-docker-deploy.sh")
for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo "✅ $script 可执行"
        else
            echo "⚠️ $script 需要执行权限: chmod +x $script"
        fi
    fi
done

echo ""
echo "📖 部署说明:"
echo "1. 快速部署: ./quick-deploy.sh"
echo "2. 完整部署: ./deploy.sh" 
echo "3. Compose部署: docker-compose up -d"
echo "4. 故障排除: 查看 DOCKER_TROUBLESHOOTING.md"
