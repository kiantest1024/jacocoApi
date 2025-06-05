#!/bin/bash

echo "🧹 清理项目..."

# 删除Python缓存
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null

# 删除空目录
find . -type d -empty -delete 2>/dev/null

# 删除临时文件
rm -rf /tmp/jacoco_reports_* 2>/dev/null

echo "✅ 清理完成"
