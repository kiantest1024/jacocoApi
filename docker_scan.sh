#!/bin/bash

# 不使用 set -e，手动处理错误
echo "JaCoCo Docker Scanner Starting..."
echo "Arguments: $@"

REPO_URL=""
COMMIT_ID=""
BRANCH=""
SERVICE_NAME=""

# 解析参数
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

# 验证参数
if [[ -z "$REPO_URL" || -z "$COMMIT_ID" || -z "$SERVICE_NAME" ]]; then
    echo "❌ Missing required parameters"
    echo "Usage: $0 --repo-url <url> --commit-id <id> --branch <branch> --service-name <name>"
    echo "Received parameters:"
    echo "  REPO_URL: $REPO_URL"
    echo "  COMMIT_ID: $COMMIT_ID"
    echo "  BRANCH: $BRANCH"
    echo "  SERVICE_NAME: $SERVICE_NAME"
    exit 1
fi

echo "Starting JaCoCo scan for $SERVICE_NAME"
echo "Repository: $REPO_URL"
echo "Commit: $COMMIT_ID"
echo "Branch: $BRANCH"

# 克隆仓库
REPO_DIR="/app/repos/$SERVICE_NAME"
rm -rf "$REPO_DIR"

echo "Cloning repository..."
if ! git clone "$REPO_URL" "$REPO_DIR"; then
    echo "Error: Failed to clone repository"
    exit 1
fi

cd "$REPO_DIR"

# 切换到指定提交
echo "Switching to commit $COMMIT_ID..."
git checkout "$COMMIT_ID" 2>/dev/null || echo "Warning: Could not checkout $COMMIT_ID, using default branch"

# 检查是否为Maven项目
if [[ ! -f "pom.xml" ]]; then
    echo "Error: Not a Maven project - no pom.xml found"
    exit 1
fi

echo "Maven project confirmed"

# 保留原始pom.xml并智能增强
echo "Enhancing original pom.xml for JaCoCo..."

# 备份原始pom.xml
cp pom.xml pom.xml.original

echo "Original pom.xml content:"
cat pom.xml

# 检查原始pom.xml是否已有JaCoCo插件
if grep -q "jacoco-maven-plugin" pom.xml; then
    echo "JaCoCo plugin already exists, keeping original pom.xml"
else
    echo "Adding JaCoCo plugin to existing pom.xml..."

    # 使用Python脚本智能增强pom.xml
    python3 << 'EOF'
import xml.etree.ElementTree as ET
import sys

try:
    # 解析原始pom.xml
    tree = ET.parse('pom.xml')
    root = tree.getroot()

    # 定义命名空间
    ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
    ET.register_namespace('', 'http://maven.apache.org/POM/4.0.0')

    # 确保有properties元素
    properties = root.find('maven:properties', ns)
    if properties is None:
        properties = ET.SubElement(root, '{http://maven.apache.org/POM/4.0.0}properties')

    # 添加JaCoCo版本属性
    jacoco_version = properties.find('maven:jacoco.version', ns)
    if jacoco_version is None:
        jacoco_version = ET.SubElement(properties, '{http://maven.apache.org/POM/4.0.0}jacoco.version')
        jacoco_version.text = '0.8.8'

    # 确保有build元素
    build = root.find('maven:build', ns)
    if build is None:
        build = ET.SubElement(root, '{http://maven.apache.org/POM/4.0.0}build')

    # 确保有plugins元素
    plugins = build.find('maven:plugins', ns)
    if plugins is None:
        plugins = ET.SubElement(build, '{http://maven.apache.org/POM/4.0.0}plugins')

    # 添加或更新surefire插件
    surefire_found = False
    for plugin in plugins.findall('maven:plugin', ns):
        artifact_id = plugin.find('maven:artifactId', ns)
        if artifact_id is not None and artifact_id.text == 'maven-surefire-plugin':
            surefire_found = True
            # 确保有argLine配置
            config = plugin.find('maven:configuration', ns)
            if config is None:
                config = ET.SubElement(plugin, '{http://maven.apache.org/POM/4.0.0}configuration')
            argline = config.find('maven:argLine', ns)
            if argline is None:
                argline = ET.SubElement(config, '{http://maven.apache.org/POM/4.0.0}argLine')
                argline.text = '${argLine}'
            break

    if not surefire_found:
        # 添加surefire插件
        surefire_plugin = ET.SubElement(plugins, '{http://maven.apache.org/POM/4.0.0}plugin')
        ET.SubElement(surefire_plugin, '{http://maven.apache.org/POM/4.0.0}groupId').text = 'org.apache.maven.plugins'
        ET.SubElement(surefire_plugin, '{http://maven.apache.org/POM/4.0.0}artifactId').text = 'maven-surefire-plugin'
        ET.SubElement(surefire_plugin, '{http://maven.apache.org/POM/4.0.0}version').text = '3.0.0-M7'
        config = ET.SubElement(surefire_plugin, '{http://maven.apache.org/POM/4.0.0}configuration')
        ET.SubElement(config, '{http://maven.apache.org/POM/4.0.0}argLine').text = '${argLine}'

    # 添加JaCoCo插件
    jacoco_plugin = ET.SubElement(plugins, '{http://maven.apache.org/POM/4.0.0}plugin')
    ET.SubElement(jacoco_plugin, '{http://maven.apache.org/POM/4.0.0}groupId').text = 'org.jacoco'
    ET.SubElement(jacoco_plugin, '{http://maven.apache.org/POM/4.0.0}artifactId').text = 'jacoco-maven-plugin'
    ET.SubElement(jacoco_plugin, '{http://maven.apache.org/POM/4.0.0}version').text = '${jacoco.version}'

    executions = ET.SubElement(jacoco_plugin, '{http://maven.apache.org/POM/4.0.0}executions')

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

    # 写入增强的pom.xml
    tree.write('pom.xml', encoding='utf-8', xml_declaration=True)
    print('POM enhancement completed successfully')

except Exception as e:
    print(f'POM enhancement failed: {e}')
    # 如果增强失败，恢复原始文件
    import shutil
    shutil.copy2('pom.xml.original', 'pom.xml')
    print('Restored original pom.xml')
EOF
fi

echo "Enhanced pom.xml content:"
cat pom.xml

# 运行Maven测试和JaCoCo
echo "Running Maven with JaCoCo..."

# 确保使用正确的Java版本
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

echo "Java version:"
java -version

echo "Maven version:"
mvn -version

# 分步执行以便调试
echo "Step 1: Clean and compile"
mvn clean compile -Dmaven.test.failure.ignore=true --batch-mode -e || echo "Compile step completed with warnings"

echo "Step 2: Compile tests"
mvn test-compile -Dmaven.test.failure.ignore=true --batch-mode -e || echo "Test compile step completed with warnings"

echo "Step 3: Run tests with JaCoCo"
echo "Running: mvn test -Dmaven.test.failure.ignore=true --batch-mode"
mvn test -Dmaven.test.failure.ignore=true --batch-mode -e || echo "Test step completed with warnings"

echo "Step 4: Generate JaCoCo report"
echo "Running: mvn jacoco:report --batch-mode"
mvn jacoco:report --batch-mode -e || echo "Report generation completed with warnings"

echo "Maven execution completed"

# 显示Maven属性和JaCoCo agent信息
echo "=== JaCoCo Agent Information ==="
echo "Checking if JaCoCo agent was properly set..."
if [ -f "target/jacoco.exec" ]; then
    echo "JaCoCo exec file exists: $(ls -la target/jacoco.exec)"
    echo "Exec file content (first 100 bytes):"
    hexdump -C target/jacoco.exec | head -5
else
    echo "No JaCoCo exec file found - this indicates JaCoCo agent was not attached"
fi

# 检查Maven属性
echo "=== Maven Properties ==="
mvn help:evaluate -Dexpression=argLine -q -DforceStdout 2>/dev/null || echo "argLine property not set"

# 显示详细的执行结果
echo "=== Maven Execution Results ==="

echo "Target directory contents:"
if [ -d "target" ]; then
    find target -type f | head -20
else
    echo "No target directory found"
fi

echo "Surefire reports:"
if [ -d "target/surefire-reports" ]; then
    ls -la target/surefire-reports/
    echo "Test results:"
    find target/surefire-reports -name "*.xml" -exec grep -l "testcase" {} \; | head -5
else
    echo "No surefire reports found"
fi

echo "JaCoCo files:"
find target -name "jacoco*" -type f | head -10

echo "JaCoCo exec file:"
if [ -f "target/jacoco.exec" ]; then
    ls -la target/jacoco.exec
    echo "Exec file size: $(wc -c < target/jacoco.exec) bytes"
else
    echo "No jacoco.exec file found"
fi

# 查找并复制报告
REPORTS_DIR="/app/reports"
mkdir -p "$REPORTS_DIR"

# 显示target目录结构用于调试
echo "Checking target directory structure..."
if [ -d "target" ]; then
    find target -type f -name "*.xml" -o -name "*.exec" | head -10
    echo "Target directory size: $(du -sh target 2>/dev/null || echo 'unknown')"
else
    echo "Warning: target directory not found"
fi

# 查找JaCoCo报告文件
echo "Looking for JaCoCo reports..."
JACOCO_XML=$(find target -name "jacoco.xml" -type f | head -1)
JACOCO_EXEC=$(find target -name "jacoco.exec" -type f | head -1)
JACOCO_HTML_DIR=$(find target -name "jacoco" -type d | head -1)

echo "Found files:"
echo "  jacoco.xml: $JACOCO_XML"
echo "  jacoco.exec: $JACOCO_EXEC"
echo "  jacoco HTML dir: $JACOCO_HTML_DIR"

if [[ -n "$JACOCO_XML" ]]; then
    echo "Found JaCoCo XML report: $JACOCO_XML"
    cp "$JACOCO_XML" "$REPORTS_DIR/jacoco.xml"

    # 显示XML文件内容的前几行用于调试
    echo "XML report preview:"
    head -10 "$JACOCO_XML"

    if [[ -n "$JACOCO_HTML_DIR" && -d "$JACOCO_HTML_DIR" ]]; then
        echo "Found JaCoCo HTML report: $JACOCO_HTML_DIR"
        cp -r "$JACOCO_HTML_DIR" "$REPORTS_DIR/html"
    fi

    echo "JaCoCo scan completed successfully"
elif [[ -n "$JACOCO_EXEC" ]]; then
    echo "Found jacoco.exec but no XML report, trying to generate report manually..."
    if mvn jacoco:report --batch-mode; then
        echo "Manual report generation succeeded"
    else
        echo "Manual report generation failed, but continuing..."
    fi

    # 重新查找XML报告
    JACOCO_XML=$(find target -name "jacoco.xml" -type f | head -1)
    if [[ -n "$JACOCO_XML" ]]; then
        echo "Successfully generated XML report: $JACOCO_XML"
        cp "$JACOCO_XML" "$REPORTS_DIR/jacoco.xml"
        echo "XML report preview:"
        head -10 "$JACOCO_XML"
    else
        echo "Failed to generate XML report, creating empty report"
        echo '<?xml version="1.0" encoding="UTF-8"?><report name="empty"><counter type="INSTRUCTION" missed="0" covered="0"/></report>' > "$REPORTS_DIR/jacoco.xml"
    fi
else
    echo "Warning: No JaCoCo reports or exec files found"
    echo "This might indicate:"
    echo "  1. No tests were executed"
    echo "  2. JaCoCo agent was not properly attached"
    echo "  3. Maven execution failed"
    echo "Creating empty report as fallback"
    echo '<?xml version="1.0" encoding="UTF-8"?><report name="empty"><counter type="INSTRUCTION" missed="0" covered="0"/></report>' > "$REPORTS_DIR/jacoco.xml"
fi

echo "Scan completed for $SERVICE_NAME"
