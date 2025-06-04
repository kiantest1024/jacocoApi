#!/bin/bash

# 测试JaCoCo扫描功能

echo "========================================"
echo "测试 JaCoCo 扫描功能"
echo "========================================"

# 检查依赖
echo "检查依赖..."

# 检查Git
if ! command -v git &> /dev/null; then
    echo "❌ Git 未安装"
    echo "Ubuntu: sudo apt install git"
    exit 1
fi
echo "✓ Git 可用"

# 检查Maven
if ! command -v mvn &> /dev/null; then
    echo "❌ Maven 未安装"
    echo "Ubuntu: sudo apt install maven"
    exit 1
fi
echo "✓ Maven 可用"

# 检查Java
if ! command -v java &> /dev/null; then
    echo "❌ Java 未安装"
    echo "Ubuntu: sudo apt install openjdk-11-jdk"
    exit 1
fi
echo "✓ Java 可用: $(java -version 2>&1 | head -n 1)"

# 检查Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python 未安装"
    exit 1
fi
echo "✓ Python 可用: $($PYTHON_CMD --version)"

echo
echo "开始测试扫描..."
echo

# 运行简化扫描测试
$PYTHON_CMD simple_scan.py

echo
echo "测试完成！"
