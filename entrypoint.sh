#!/bin/bash

# Docker容器入口点包装脚本
echo "Docker Container Starting..."
echo "Received arguments: $@"

# 检查参数
if [ $# -eq 0 ]; then
    echo "Usage: docker run jacoco-scanner:latest --repo-url <url> --commit-id <id> --branch <branch> --service-name <name>"
    exit 1
fi

# 执行实际的扫描脚本
exec /app/scripts/docker_scan.sh "$@"
