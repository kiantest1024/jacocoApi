#!/bin/bash

set -e

REPO_URL=""
COMMIT_ID=""
BRANCH=""
SERVICE_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --repo-url)
            REPO_URL="$2"
            shift 2
            ;;
        --commit-id)
            COMMIT_ID="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --service-name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        *)
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
done

if [[ -z "$REPO_URL" || -z "$COMMIT_ID" || -z "$SERVICE_NAME" ]]; then
    echo "Missing required parameters"
    echo "Usage: $0 --repo-url <url> --commit-id <id> --branch <branch> --service-name <name>"
    exit 1
fi

echo "Starting JaCoCo scan for $SERVICE_NAME"
echo "Repository: $REPO_URL"
echo "Commit: $COMMIT_ID"
echo "Branch: $BRANCH"

# 克隆仓库
REPO_DIR="/app/repos/$SERVICE_NAME"
rm -rf "$REPO_DIR"
git clone "$REPO_URL" "$REPO_DIR"
cd "$REPO_DIR"

# 切换到指定提交
git checkout "$COMMIT_ID" || echo "Warning: Could not checkout $COMMIT_ID"

# 检查是否为Maven项目
if [[ ! -f "pom.xml" ]]; then
    echo "Error: Not a Maven project"
    exit 1
fi

# 增强pom.xml支持JaCoCo
echo "Enhancing pom.xml for JaCoCo..."

# 创建简单的pom.xml增强脚本
cat > enhance_pom.py << 'EOF'
import xml.etree.ElementTree as ET
import sys

try:
    # 注册命名空间
    ET.register_namespace('', 'http://maven.apache.org/POM/4.0.0')

    tree = ET.parse('pom.xml')
    root = tree.getroot()

    # 定义命名空间
    ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}

    # 查找或创建build元素
    build = root.find('maven:build', ns)
    if build is None:
        build = ET.SubElement(root, '{http://maven.apache.org/POM/4.0.0}build')

    # 查找或创建plugins元素
    plugins = build.find('maven:plugins', ns)
    if plugins is None:
        plugins = ET.SubElement(build, '{http://maven.apache.org/POM/4.0.0}plugins')

    # 检查是否已有JaCoCo插件
    jacoco_exists = False
    for plugin in plugins.findall('maven:plugin', ns):
        artifact_id = plugin.find('maven:artifactId', ns)
        if artifact_id is not None and artifact_id.text == 'jacoco-maven-plugin':
            jacoco_exists = True
            break

    if not jacoco_exists:
        # 添加JaCoCo插件
        plugin = ET.SubElement(plugins, '{http://maven.apache.org/POM/4.0.0}plugin')
        ET.SubElement(plugin, '{http://maven.apache.org/POM/4.0.0}groupId').text = 'org.jacoco'
        ET.SubElement(plugin, '{http://maven.apache.org/POM/4.0.0}artifactId').text = 'jacoco-maven-plugin'
        ET.SubElement(plugin, '{http://maven.apache.org/POM/4.0.0}version').text = '0.8.7'

        executions = ET.SubElement(plugin, '{http://maven.apache.org/POM/4.0.0}executions')

        # prepare-agent execution
        execution1 = ET.SubElement(executions, '{http://maven.apache.org/POM/4.0.0}execution')
        ET.SubElement(execution1, '{http://maven.apache.org/POM/4.0.0}id').text = 'prepare-agent'
        goals1 = ET.SubElement(execution1, '{http://maven.apache.org/POM/4.0.0}goals')
        ET.SubElement(goals1, '{http://maven.apache.org/POM/4.0.0}goal').text = 'prepare-agent'

        # report execution
        execution2 = ET.SubElement(executions, '{http://maven.apache.org/POM/4.0.0}execution')
        ET.SubElement(execution2, '{http://maven.apache.org/POM/4.0.0}id').text = 'report'
        ET.SubElement(execution2, '{http://maven.apache.org/POM/4.0.0}phase').text = 'test'
        goals2 = ET.SubElement(execution2, '{http://maven.apache.org/POM/4.0.0}goals')
        ET.SubElement(goals2, '{http://maven.apache.org/POM/4.0.0}goal').text = 'report'

        print('JaCoCo plugin added to pom.xml')
    else:
        print('JaCoCo plugin already exists in pom.xml')

    # 写入文件
    tree.write('pom.xml', encoding='utf-8', xml_declaration=True)
    print('POM enhancement completed successfully')

except Exception as e:
    print(f'POM enhancement failed: {e}')
    sys.exit(1)
EOF

# 运行pom.xml增强脚本
python3 enhance_pom.py

# 运行Maven测试和JaCoCo
echo "Running Maven test with JaCoCo..."
mvn clean test jacoco:report \
    -Dmaven.test.failure.ignore=true \
    -Dproject.build.sourceEncoding=UTF-8 \
    -Dmaven.compiler.source=11 \
    -Dmaven.compiler.target=11 \
    --batch-mode \
    || echo "Maven execution completed with warnings"

# 查找并复制报告
REPORTS_DIR="/app/reports"
mkdir -p "$REPORTS_DIR"

# 查找JaCoCo报告
JACOCO_XML=$(find target -name "jacoco.xml" -type f | head -1)
JACOCO_HTML_DIR=$(find target -name "jacoco" -type d | head -1)

if [[ -n "$JACOCO_XML" ]]; then
    echo "Found JaCoCo XML report: $JACOCO_XML"
    cp "$JACOCO_XML" "$REPORTS_DIR/jacoco.xml"
    
    if [[ -n "$JACOCO_HTML_DIR" && -d "$JACOCO_HTML_DIR" ]]; then
        echo "Found JaCoCo HTML report: $JACOCO_HTML_DIR"
        cp -r "$JACOCO_HTML_DIR" "$REPORTS_DIR/html"
    fi
    
    echo "JaCoCo scan completed successfully"
else
    echo "Warning: No JaCoCo reports found"
    # 创建空报告
    echo '<?xml version="1.0" encoding="UTF-8"?><report name="empty"><counter type="INSTRUCTION" missed="0" covered="0"/></report>' > "$REPORTS_DIR/jacoco.xml"
fi

echo "Scan completed for $SERVICE_NAME"
