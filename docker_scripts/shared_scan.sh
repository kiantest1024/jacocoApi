#!/bin/bash
# 共享容器内的扫描脚本
# 支持并发处理多个扫描任务

set -e

# 检查参数
if [ $# -ne 1 ]; then
    echo "用法: $0 <task_config.json>"
    exit 1
fi

TASK_CONFIG_FILE="$1"
TASK_DIR=$(dirname "$TASK_CONFIG_FILE")

# 检查配置文件是否存在
if [ ! -f "$TASK_CONFIG_FILE" ]; then
    echo "错误: 任务配置文件不存在: $TASK_CONFIG_FILE"
    exit 1
fi

# 读取任务配置
REPO_URL=$(jq -r '.repo_url' "$TASK_CONFIG_FILE")
COMMIT_ID=$(jq -r '.commit_id' "$TASK_CONFIG_FILE")
BRANCH_NAME=$(jq -r '.branch_name' "$TASK_CONFIG_FILE")
SERVICE_NAME=$(jq -r '.service_name' "$TASK_CONFIG_FILE")
REQUEST_ID=$(jq -r '.request_id' "$TASK_CONFIG_FILE")

echo "开始JaCoCo扫描..."
echo "任务ID: $REQUEST_ID"
echo "仓库: $REPO_URL"
echo "提交: $COMMIT_ID"
echo "分支: $BRANCH_NAME"
echo "服务: $SERVICE_NAME"

# 创建任务专用的工作目录
REPO_DIR="$TASK_DIR/repo"
REPORTS_DIR="$TASK_DIR/reports"

mkdir -p "$REPO_DIR"
mkdir -p "$REPORTS_DIR"

# 初始化结果文件
RESULT_FILE="$TASK_DIR/scan_result.json"
cat > "$RESULT_FILE" << EOF
{
    "status": "running",
    "request_id": "$REQUEST_ID",
    "start_time": "$(date -Iseconds)",
    "repo_url": "$REPO_URL",
    "commit_id": "$COMMIT_ID"
}
EOF

# 错误处理函数
handle_error() {
    local error_msg="$1"
    local exit_code="$2"
    
    echo "错误: $error_msg"
    
    cat > "$RESULT_FILE" << EOF
{
    "status": "failed",
    "request_id": "$REQUEST_ID",
    "error": "$error_msg",
    "return_code": $exit_code,
    "end_time": "$(date -Iseconds)"
}
EOF
    
    exit $exit_code
}

# 设置错误陷阱
trap 'handle_error "脚本执行异常" $?' ERR

# 1. 克隆或更新仓库
echo "克隆仓库到: $REPO_DIR"
if [ -d "$REPO_DIR/.git" ]; then
    echo "更新现有仓库..."
    cd "$REPO_DIR"
    git fetch origin
    git reset --hard "$COMMIT_ID"
else
    echo "克隆新仓库..."
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
    git checkout "$COMMIT_ID"
fi

# 2. 检查是否为Maven项目
if [ ! -f "pom.xml" ]; then
    handle_error "不是Maven项目，未找到pom.xml" 1
fi

echo "找到Maven项目"

# 3. 检查项目源代码
echo "检查项目源代码..."
MAIN_JAVA_DIR="src/main/java"
TEST_JAVA_DIR="src/test/java"

if [ ! -d "$MAIN_JAVA_DIR" ]; then
    handle_error "未找到主代码目录: $MAIN_JAVA_DIR" 1
fi

MAIN_CODE_COUNT=$(find "$MAIN_JAVA_DIR" -name "*.java" | wc -l)
TEST_CODE_COUNT=$(find "$TEST_JAVA_DIR" -name "*.java" 2>/dev/null | wc -l)

echo "主代码文件数: $MAIN_CODE_COUNT"
echo "测试代码文件数: $TEST_CODE_COUNT"

if [ "$MAIN_CODE_COUNT" -eq 0 ]; then
    handle_error "未找到Java源代码文件" 1
fi

# 4. 备份原始pom.xml
echo "备份原始pom.xml..."
cp pom.xml pom.xml.backup

# 5. 增强pom.xml以支持JaCoCo
echo "增强pom.xml以支持JaCoCo..."

# 检查是否已有JaCoCo配置
if grep -q "jacoco-maven-plugin" pom.xml; then
    echo "pom.xml已包含JaCoCo配置"
else
    echo "添加JaCoCo配置到pom.xml..."
    
    # 使用Python脚本增强pom.xml（如果可用）
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "
import xml.etree.ElementTree as ET
import sys

# 读取pom.xml
tree = ET.parse('pom.xml')
root = tree.getroot()

# 定义命名空间
ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}

# 添加JaCoCo插件
plugins = root.find('.//maven:plugins', ns)
if plugins is None:
    build = root.find('.//maven:build', ns)
    if build is None:
        build = ET.SubElement(root, 'build')
    plugins = ET.SubElement(build, 'plugins')

# 创建JaCoCo插件配置
jacoco_plugin = ET.SubElement(plugins, 'plugin')
ET.SubElement(jacoco_plugin, 'groupId').text = 'org.jacoco'
ET.SubElement(jacoco_plugin, 'artifactId').text = 'jacoco-maven-plugin'
ET.SubElement(jacoco_plugin, 'version').text = '0.8.7'

executions = ET.SubElement(jacoco_plugin, 'executions')
execution1 = ET.SubElement(executions, 'execution')
goals1 = ET.SubElement(execution1, 'goals')
ET.SubElement(goals1, 'goal').text = 'prepare-agent'

execution2 = ET.SubElement(executions, 'execution')
ET.SubElement(execution2, 'id').text = 'report'
ET.SubElement(execution2, 'phase').text = 'test'
goals2 = ET.SubElement(execution2, 'goals')
ET.SubElement(goals2, 'goal').text = 'report'

# 保存文件
tree.write('pom.xml', encoding='utf-8', xml_declaration=True)
print('JaCoCo配置已添加')
"
    else
        echo "警告: 无法自动添加JaCoCo配置，使用现有配置"
    fi
fi

# 6. 运行Maven测试和JaCoCo
echo "运行Maven测试和JaCoCo..."

# 首先尝试离线模式
echo "尝试离线模式..."
if mvn clean compile test-compile test jacoco:report \
    -Dmaven.test.failure.ignore=true \
    -Dproject.build.sourceEncoding=UTF-8 \
    -Dmaven.compiler.source=11 \
    -Dmaven.compiler.target=11 \
    -o --batch-mode; then
    echo "离线模式扫描成功"
    SCAN_MODE="offline"
else
    echo "离线模式失败，尝试在线模式..."
    if mvn clean compile test-compile test jacoco:report \
        -Dmaven.test.failure.ignore=true \
        -Dproject.build.sourceEncoding=UTF-8 \
        -Dmaven.compiler.source=11 \
        -Dmaven.compiler.target=11 \
        --batch-mode; then
        echo "在线模式扫描成功"
        SCAN_MODE="online"
    else
        handle_error "Maven扫描失败" 1
    fi
fi

# 7. 查找并复制JaCoCo报告
echo "查找JaCoCo报告..."

# 可能的报告位置
POSSIBLE_LOCATIONS=(
    "target/site/jacoco/jacoco.xml"
    "target/jacoco-reports/jacoco.xml"
    "target/jacoco/jacoco.xml"
    "target/reports/jacoco/jacoco.xml"
)

JACOCO_XML=""
for location in "${POSSIBLE_LOCATIONS[@]}"; do
    if [ -f "$location" ]; then
        JACOCO_XML="$location"
        echo "找到JaCoCo XML报告: $location"
        break
    fi
done

if [ -z "$JACOCO_XML" ]; then
    handle_error "未找到JaCoCo XML报告" 1
fi

# 复制报告到结果目录
echo "复制报告到结果目录..."
cp "$JACOCO_XML" "$REPORTS_DIR/jacoco.xml"

# 复制HTML报告（如果存在）
HTML_DIR=$(dirname "$JACOCO_XML")
if [ -f "$HTML_DIR/index.html" ]; then
    echo "复制HTML报告..."
    cp -r "$HTML_DIR"/* "$REPORTS_DIR/"
fi

# 复制CSV报告（如果存在）
CSV_REPORT=$(dirname "$JACOCO_XML")/jacoco.csv
if [ -f "$CSV_REPORT" ]; then
    echo "复制CSV报告..."
    cp "$CSV_REPORT" "$REPORTS_DIR/"
fi

# 8. 生成最终结果
echo "生成扫描结果..."

cat > "$RESULT_FILE" << EOF
{
    "status": "completed",
    "request_id": "$REQUEST_ID",
    "repo_url": "$REPO_URL",
    "commit_id": "$COMMIT_ID",
    "branch_name": "$BRANCH_NAME",
    "service_name": "$SERVICE_NAME",
    "scan_mode": "$SCAN_MODE",
    "reports_dir": "$REPORTS_DIR",
    "main_code_files": $MAIN_CODE_COUNT,
    "test_code_files": $TEST_CODE_COUNT,
    "start_time": "$(jq -r '.start_time' "$TASK_CONFIG_FILE" 2>/dev/null || echo "unknown")",
    "end_time": "$(date -Iseconds)",
    "return_code": 0
}
EOF

echo "JaCoCo扫描完成！"
echo "结果文件: $RESULT_FILE"
echo "报告目录: $REPORTS_DIR"
