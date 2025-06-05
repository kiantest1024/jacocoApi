#!/bin/bash

echo "🧪 测试Docker镜像入口点..."

# 测试1: 检查脚本是否可执行
echo "📋 测试1: 检查脚本执行权限"
docker run --rm jacoco-scanner:latest ls -la /app/scripts/docker_scan.sh

# 测试2: 测试bash是否可用
echo "📋 测试2: 检查bash路径"
docker run --rm jacoco-scanner:latest which bash

# 测试3: 直接执行脚本（无参数）
echo "📋 测试3: 直接执行脚本"
docker run --rm jacoco-scanner:latest

# 测试4: 执行脚本帮助
echo "📋 测试4: 执行脚本帮助"
docker run --rm jacoco-scanner:latest --help

echo "✅ 测试完成"
