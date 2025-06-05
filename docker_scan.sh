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
python3 -c "
import xml.etree.ElementTree as ET
import sys

try:
    tree = ET.parse('pom.xml')
    root = tree.getroot()
    
    # 添加JaCoCo插件
    plugins = root.find('.//{http://maven.apache.org/POM/4.0.0}plugins')
    if plugins is None:
        build = root.find('.//{http://maven.apache.org/POM/4.0.0}build')
        if build is None:
            build = ET.SubElement(root, 'build')
        plugins = ET.SubElement(build, 'plugins')
    
    # 检查是否已有JaCoCo插件
    jacoco_exists = False
    for plugin in plugins.findall('.//{http://maven.apache.org/POM/4.0.0}plugin'):
        artifact_id = plugin.find('.//{http://maven.apache.org/POM/4.0.0}artifactId')
        if artifact_id is not None and artifact_id.text == 'jacoco-maven-plugin':
            jacoco_exists = True
            break
    
    if not jacoco_exists:
        plugin = ET.SubElement(plugins, 'plugin')
        ET.SubElement(plugin, 'groupId').text = 'org.jacoco'
        ET.SubElement(plugin, 'artifactId').text = 'jacoco-maven-plugin'
        ET.SubElement(plugin, 'version').text = '0.8.7'
        
        executions = ET.SubElement(plugin, 'executions')
        execution = ET.SubElement(executions, 'execution')
        ET.SubElement(execution, 'id').text = 'prepare-agent'
        goals = ET.SubElement(execution, 'goals')
        ET.SubElement(goals, 'goal').text = 'prepare-agent'
        
        execution2 = ET.SubElement(executions, 'execution')
        ET.SubElement(execution2, 'id').text = 'report'
        ET.SubElement(execution2, 'phase').text = 'test'
        goals2 = ET.SubElement(execution2, 'goals')
        ET.SubElement(goals2, 'goal').text = 'report'
    
    tree.write('pom.xml', encoding='utf-8', xml_declaration=True)
    print('POM enhanced successfully')
except Exception as e:
    print(f'POM enhancement failed: {e}')
"

# 运行Maven测试和JaCoCo
echo "Running Maven test with JaCoCo..."
mvn clean test jacoco:report -Dmaven.test.failure.ignore=true -Dproject.build.sourceEncoding=UTF-8 || echo "Maven execution completed with warnings"

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
