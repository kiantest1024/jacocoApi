#!/bin/bash

echo "🔍 调试Docker JaCoCo扫描..."

# 创建调试目录
DEBUG_DIR="/tmp/debug_jacoco_$(date +%s)"
mkdir -p "$DEBUG_DIR"

echo "📁 调试目录: $DEBUG_DIR"

# 运行Docker扫描并保存详细输出
echo "🚀 运行Docker扫描..."
docker run --rm \
  -v "$DEBUG_DIR:/app/reports" \
  jacoco-scanner:latest \
  --repo-url http://172.16.1.30/kian/jacocotest.git \
  --commit-id 5ea76b4989a17153eade57d7d55609ebad7fdd9e \
  --branch main \
  --service-name jacocotest \
  > "$DEBUG_DIR/docker_output.log" 2>&1

echo "📋 Docker扫描完成，检查结果..."

# 检查生成的文件
echo "📂 生成的文件:"
ls -la "$DEBUG_DIR/"

# 检查JaCoCo XML报告内容
if [ -f "$DEBUG_DIR/jacoco.xml" ]; then
    echo "📄 JaCoCo XML报告内容:"
    head -20 "$DEBUG_DIR/jacoco.xml"
    echo "..."
    echo "XML文件大小: $(wc -c < "$DEBUG_DIR/jacoco.xml") bytes"
else
    echo "❌ 未找到jacoco.xml文件"
fi

# 检查HTML报告
if [ -d "$DEBUG_DIR/html" ]; then
    echo "📊 HTML报告目录:"
    ls -la "$DEBUG_DIR/html/"
else
    echo "❌ 未找到HTML报告目录"
fi

# 显示Docker输出日志
echo "📝 Docker扫描日志:"
cat "$DEBUG_DIR/docker_output.log"

echo "✅ 调试完成，调试文件保存在: $DEBUG_DIR"
