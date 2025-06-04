#!/bin/bash

# Ubuntu 环境设置脚本

echo "设置 Ubuntu 环境..."

# 设置脚本执行权限
chmod +x quick_start.sh
chmod +x start_ubuntu.sh
chmod +x setup_ubuntu.sh

echo "✓ 脚本权限已设置"

# 检查并安装基础依赖
echo "检查系统依赖..."

# 更新包列表
sudo apt update

# 安装 Python3 和相关工具
sudo apt install -y python3 python3-pip python3-venv python3-dev

# 安装 Redis（可选）
read -p "是否安装 Redis? (y/N): " install_redis
if [[ $install_redis =~ ^[Yy]$ ]]; then
    sudo apt install -y redis-server
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
    echo "✓ Redis 已安装并启动"
fi

# 安装 Docker（可选）
read -p "是否安装 Docker? (y/N): " install_docker
if [[ $install_docker =~ ^[Yy]$ ]]; then
    sudo apt install -y docker.io
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
    echo "✓ Docker 已安装"
    echo "⚠ 请重新登录以使 Docker 权限生效"
fi

# 安装 Java 和 Maven（用于 JaCoCo 扫描）
read -p "是否安装 Java 和 Maven? (y/N): " install_java
if [[ $install_java =~ ^[Yy]$ ]]; then
    sudo apt install -y openjdk-11-jdk maven
    echo "✓ Java 和 Maven 已安装"
fi

echo
echo "🎉 Ubuntu 环境设置完成！"
echo
echo "现在可以使用以下命令启动服务："
echo "  ./start_ubuntu.sh     # 简化启动"
echo "  ./quick_start.sh      # 完整启动（需要 Redis）"
echo
