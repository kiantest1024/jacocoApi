#!/bin/bash

echo "🧪 测试HTML报告生成..."

# 重建Docker镜像
echo "🔨 重建Docker镜像..."
docker rmi jacoco-scanner:latest 2>/dev/null || true
docker build -t jacoco-scanner:latest .

if [ $? -ne 0 ]; then
    echo "❌ Docker镜像构建失败"
    exit 1
fi

echo "✅ Docker镜像构建成功"

# 创建测试目录
TEST_DIR="/tmp/html_report_test_$(date +%s)"
mkdir -p "$TEST_DIR"

echo "📁 测试目录: $TEST_DIR"

# 运行Docker扫描
echo "🚀 运行Docker扫描..."
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

# 检查XML报告
if [ -f "$TEST_DIR/jacoco.xml" ]; then
    echo "✅ XML报告存在"
    echo "XML文件大小: $(wc -c < "$TEST_DIR/jacoco.xml") bytes"
else
    echo "❌ XML报告不存在"
fi

# 检查HTML报告
if [ -d "$TEST_DIR/html" ]; then
    echo "✅ HTML报告目录存在"
    echo "HTML报告内容:"
    ls -la "$TEST_DIR/html/"
    
    if [ -f "$TEST_DIR/html/index.html" ]; then
        echo "✅ HTML主页面存在"
        echo "HTML文件大小: $(wc -c < "$TEST_DIR/html/index.html") bytes"
        
        # 检查HTML内容
        if grep -q "JaCoCo Coverage Report" "$TEST_DIR/html/index.html"; then
            echo "✅ HTML报告内容正确"
        else
            echo "⚠️ HTML报告内容可能有问题"
        fi
        
        # 显示HTML内容预览
        echo "HTML内容预览:"
        head -20 "$TEST_DIR/html/index.html"
    else
        echo "❌ HTML主页面不存在"
    fi
else
    echo "❌ HTML报告目录不存在"
fi

echo "🔍 测试完成，结果保存在: $TEST_DIR"

# 提供访问建议
if [ -f "$TEST_DIR/html/index.html" ]; then
    echo ""
    echo "💡 可以通过以下方式查看HTML报告:"
    echo "   1. 在浏览器中打开: file://$TEST_DIR/html/index.html"
    echo "   2. 或者复制到Web服务器目录中访问"
fi
