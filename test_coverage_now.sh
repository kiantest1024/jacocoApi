#!/bin/bash

echo "🚀 快速测试JaCoCo覆盖率修复..."

# 重建Docker镜像
echo "🔨 重建Docker镜像..."
docker rmi jacoco-scanner:latest 2>/dev/null || true
docker build -t jacoco-scanner:latest . --no-cache

if [ $? -ne 0 ]; then
    echo "❌ Docker镜像构建失败"
    exit 1
fi

echo "✅ Docker镜像构建成功"

# 创建测试目录
TEST_DIR="/tmp/jacoco_test_$(date +%s)"
mkdir -p "$TEST_DIR"

echo "📁 测试目录: $TEST_DIR"

# 运行Docker扫描
echo "🧪 运行Docker扫描..."
docker run --rm \
  -v "$TEST_DIR:/app/reports" \
  jacoco-scanner:latest \
  --repo-url http://172.16.1.30/kian/jacocotest.git \
  --commit-id 5ea76b4989a17153eade57d7d55609ebad7fdd9e \
  --branch main \
  --service-name jacocotest

echo "📊 检查扫描结果..."

# 检查生成的文件
echo "📂 生成的文件:"
ls -la "$TEST_DIR/"

# 检查JaCoCo XML内容
if [ -f "$TEST_DIR/jacoco.xml" ]; then
    echo "📄 JaCoCo XML文件大小: $(wc -c < "$TEST_DIR/jacoco.xml") bytes"
    echo "📄 JaCoCo XML内容预览:"
    head -20 "$TEST_DIR/jacoco.xml"
    
    # 检查是否包含实际覆盖率数据
    if grep -q 'covered="[1-9]' "$TEST_DIR/jacoco.xml"; then
        echo "✅ 发现覆盖率数据！"
        grep 'covered=' "$TEST_DIR/jacoco.xml" | head -5
    else
        echo "❌ 仍然没有覆盖率数据"
    fi
else
    echo "❌ 未找到jacoco.xml文件"
fi

echo "✅ 测试完成，结果保存在: $TEST_DIR"
