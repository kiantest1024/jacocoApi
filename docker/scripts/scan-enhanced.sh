#!/bin/bash
# JaCoCo Docker 扫描脚本

set -e

REPO_URL=""
COMMIT_ID=""
BRANCH=""
SERVICE_NAME=""

log_info() {
    echo "[$(date '+%H:%M:%S')] INFO: $1"
}

log_error() {
    echo "[$(date '+%H:%M:%S')] ERROR: $1" >&2
}

log_success() {
    echo "[$(date '+%H:%M:%S')] SUCCESS: $1"
}

log_warning() {
    echo "[$(date '+%H:%M:%S')] WARNING: $1"
}

# 解析命令行参数
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
            log_error "未知参数: $1"
            exit 1
            ;;
    esac
done

# 验证必需参数
if [[ -z "$REPO_URL" || -z "$COMMIT_ID" || -z "$SERVICE_NAME" ]]; then
    log_error "缺少必需参数"
    echo "用法: $0 --repo-url <URL> --commit-id <ID> --branch <BRANCH> --service-name <name>"
    exit 1
fi

log_info "开始JaCoCo扫描..."
log_info "仓库: $REPO_URL"
log_info "提交: $COMMIT_ID"
log_info "分支: $BRANCH"
log_info "服务: $SERVICE_NAME"

# 显示环境信息
log_info "Java: $(java -version 2>&1 | head -1)"
log_info "Maven: $(mvn --version | head -1)"

# 设置路径
REPO_DIR="/app/repos/$SERVICE_NAME"
REPORTS_DIR="/app/reports"
LOG_FILE="/app/logs/scan-${SERVICE_NAME}-$(date +%Y%m%d-%H%M%S).log"

# 创建目录
mkdir -p "$REPO_DIR"
mkdir -p "$REPORTS_DIR"
mkdir -p "/app/logs"

# 重定向日志
exec > >(tee -a "$LOG_FILE")
exec 2>&1

log_info "日志文件: $LOG_FILE"

# 克隆或更新仓库
if [[ -d "$REPO_DIR/.git" ]]; then
    log_info "更新现有仓库..."
    cd "$REPO_DIR"
    git fetch origin
    git reset --hard "$COMMIT_ID"
else
    log_info "克隆仓库..."
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
    git checkout "$COMMIT_ID"
fi

log_success "仓库准备完成"

# 检查是否为Maven项目
if [[ ! -f "pom.xml" ]]; then
    log_error "不是Maven项目，未找到pom.xml"
    exit 1
fi

log_success "找到Maven项目"

# 显示项目结构
log_info "项目结构:"
tree -L 3 . || find . -type d -maxdepth 3

# 检查源代码和测试代码
SRC_MAIN_JAVA="src/main/java"
SRC_TEST_JAVA="src/test/java"

if [[ -d "$SRC_MAIN_JAVA" ]]; then
    MAIN_JAVA_COUNT=$(find "$SRC_MAIN_JAVA" -name "*.java" | wc -l)
    log_info "主代码文件数: $MAIN_JAVA_COUNT"
else
    log_warning "未找到主代码目录: $SRC_MAIN_JAVA"
    MAIN_JAVA_COUNT=0
fi

if [[ -d "$SRC_TEST_JAVA" ]]; then
    TEST_JAVA_COUNT=$(find "$SRC_TEST_JAVA" -name "*.java" | wc -l)
    log_info "测试代码文件数: $TEST_JAVA_COUNT"
else
    log_warning "未找到测试代码目录: $SRC_TEST_JAVA"
    TEST_JAVA_COUNT=0
fi

if [[ $TEST_JAVA_COUNT -eq 0 ]]; then
    log_warning "项目没有测试代码，覆盖率将为0%"
fi

# 备份原始pom.xml
log_info "备份原始pom.xml..."
cp pom.xml pom.xml.backup

# 增强pom.xml以支持JaCoCo
log_info "增强pom.xml以支持JaCoCo..."

# 检查是否已有JaCoCo插件
if grep -q "jacoco-maven-plugin" pom.xml; then
    log_info "JaCoCo插件已存在，跳过增强"
else
    log_info "添加JaCoCo插件配置..."
    
    # 创建增强的pom.xml
    python3 << 'EOF'
import xml.etree.ElementTree as ET
import sys

try:
    # 解析pom.xml
    tree = ET.parse('pom.xml')
    root = tree.getroot()
    
    # 定义命名空间
    ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
    ET.register_namespace('', 'http://maven.apache.org/POM/4.0.0')
    
    # 添加JaCoCo属性
    properties = root.find('maven:properties', ns)
    if properties is None:
        properties = ET.SubElement(root, 'properties')

    jacoco_version = ET.SubElement(properties, 'jacoco.version')
    jacoco_version.text = '0.8.8'

    # 添加其他必要属性
    maven_compiler_source = ET.SubElement(properties, 'maven.compiler.source')
    maven_compiler_source.text = '11'
    maven_compiler_target = ET.SubElement(properties, 'maven.compiler.target')
    maven_compiler_target.text = '11'
    project_encoding = ET.SubElement(properties, 'project.build.sourceEncoding')
    project_encoding.text = 'UTF-8'

    junit_version = ET.SubElement(properties, 'junit.version')
    junit_version.text = '5.9.2'
    mockito_version = ET.SubElement(properties, 'mockito.version')
    mockito_version.text = '4.11.0'
    assertj_version = ET.SubElement(properties, 'assertj.version')
    assertj_version.text = '3.24.2'
    
    # 添加依赖
    dependencies = root.find('maven:dependencies', ns)
    if dependencies is None:
        dependencies = ET.SubElement(root, 'dependencies')

    # JUnit 5 依赖
    junit_dep = ET.SubElement(dependencies, 'dependency')
    junit_group = ET.SubElement(junit_dep, 'groupId')
    junit_group.text = 'org.junit.jupiter'
    junit_artifact = ET.SubElement(junit_dep, 'artifactId')
    junit_artifact.text = 'junit-jupiter'
    junit_ver = ET.SubElement(junit_dep, 'version')
    junit_ver.text = '${junit.version}'
    junit_scope = ET.SubElement(junit_dep, 'scope')
    junit_scope.text = 'test'

    # Mockito 依赖
    mockito_dep = ET.SubElement(dependencies, 'dependency')
    mockito_group = ET.SubElement(mockito_dep, 'groupId')
    mockito_group.text = 'org.mockito'
    mockito_artifact = ET.SubElement(mockito_dep, 'artifactId')
    mockito_artifact.text = 'mockito-core'
    mockito_ver = ET.SubElement(mockito_dep, 'version')
    mockito_ver.text = '${mockito.version}'
    mockito_scope = ET.SubElement(mockito_dep, 'scope')
    mockito_scope.text = 'test'

    # Mockito JUnit Jupiter 依赖
    mockito_junit_dep = ET.SubElement(dependencies, 'dependency')
    mockito_junit_group = ET.SubElement(mockito_junit_dep, 'groupId')
    mockito_junit_group.text = 'org.mockito'
    mockito_junit_artifact = ET.SubElement(mockito_junit_dep, 'artifactId')
    mockito_junit_artifact.text = 'mockito-junit-jupiter'
    mockito_junit_ver = ET.SubElement(mockito_junit_dep, 'version')
    mockito_junit_ver.text = '${mockito.version}'
    mockito_junit_scope = ET.SubElement(mockito_junit_dep, 'scope')
    mockito_junit_scope.text = 'test'

    # AssertJ 依赖
    assertj_dep = ET.SubElement(dependencies, 'dependency')
    assertj_group = ET.SubElement(assertj_dep, 'groupId')
    assertj_group.text = 'org.assertj'
    assertj_artifact = ET.SubElement(assertj_dep, 'artifactId')
    assertj_artifact.text = 'assertj-core'
    assertj_ver = ET.SubElement(assertj_dep, 'version')
    assertj_ver.text = '${assertj.version}'
    assertj_scope = ET.SubElement(assertj_dep, 'scope')
    assertj_scope.text = 'test'

    # 查找或创建build节点
    build = root.find('maven:build', ns)
    if build is None:
        build = ET.SubElement(root, 'build')

    # 查找或创建plugins节点
    plugins = build.find('maven:plugins', ns)
    if plugins is None:
        plugins = ET.SubElement(build, 'plugins')
    
    # Maven Compiler Plugin
    compiler_plugin = ET.SubElement(plugins, 'plugin')
    comp_group = ET.SubElement(compiler_plugin, 'groupId')
    comp_group.text = 'org.apache.maven.plugins'
    comp_artifact = ET.SubElement(compiler_plugin, 'artifactId')
    comp_artifact.text = 'maven-compiler-plugin'
    comp_version = ET.SubElement(compiler_plugin, 'version')
    comp_version.text = '3.11.0'
    comp_config = ET.SubElement(compiler_plugin, 'configuration')
    comp_source = ET.SubElement(comp_config, 'source')
    comp_source.text = '11'
    comp_target = ET.SubElement(comp_config, 'target')
    comp_target.text = '11'

    # Maven Surefire Plugin (for JUnit 5)
    surefire_plugin = ET.SubElement(plugins, 'plugin')
    sure_group = ET.SubElement(surefire_plugin, 'groupId')
    sure_group.text = 'org.apache.maven.plugins'
    sure_artifact = ET.SubElement(surefire_plugin, 'artifactId')
    sure_artifact.text = 'maven-surefire-plugin'
    sure_version = ET.SubElement(surefire_plugin, 'version')
    sure_version.text = '3.0.0-M9'
    sure_config = ET.SubElement(surefire_plugin, 'configuration')
    sure_fail_ignore = ET.SubElement(sure_config, 'testFailureIgnore')
    sure_fail_ignore.text = 'true'

    # 添加JaCoCo插件
    jacoco_plugin = ET.SubElement(plugins, 'plugin')

    group_id = ET.SubElement(jacoco_plugin, 'groupId')
    group_id.text = 'org.jacoco'

    artifact_id = ET.SubElement(jacoco_plugin, 'artifactId')
    artifact_id.text = 'jacoco-maven-plugin'

    version = ET.SubElement(jacoco_plugin, 'version')
    version.text = '${jacoco.version}'

    executions = ET.SubElement(jacoco_plugin, 'executions')

    # prepare-agent execution
    execution1 = ET.SubElement(executions, 'execution')
    exec1_id = ET.SubElement(execution1, 'id')
    exec1_id.text = 'prepare-agent'
    exec1_goals = ET.SubElement(execution1, 'goals')
    exec1_goal = ET.SubElement(exec1_goals, 'goal')
    exec1_goal.text = 'prepare-agent'

    # report execution
    execution2 = ET.SubElement(executions, 'execution')
    exec2_id = ET.SubElement(execution2, 'id')
    exec2_id.text = 'report'
    exec2_phase = ET.SubElement(execution2, 'phase')
    exec2_phase.text = 'test'
    exec2_goals = ET.SubElement(execution2, 'goals')
    exec2_goal = ET.SubElement(exec2_goals, 'goal')
    exec2_goal.text = 'report'
    
    # 保存文件
    tree.write('pom.xml', encoding='utf-8', xml_declaration=True)
    print("JaCoCo插件配置添加成功")
    
except Exception as e:
    print(f"增强pom.xml失败: {e}")
    sys.exit(1)
EOF

    if [[ $? -eq 0 ]]; then
        log_success "pom.xml增强成功"
    else
        log_warning "pom.xml增强失败，使用原始文件"
        cp pom.xml.backup pom.xml
    fi
fi

# 显示最终的pom.xml关键部分
log_info "pom.xml关键配置:"
grep -A 20 "jacoco-maven-plugin" pom.xml || log_warning "未找到JaCoCo插件配置"

# 设置Maven环境变量
export MAVEN_OPTS="-Xmx2g -XX:MetaspaceSize=512m"
export JAVA_OPTS="-Xmx2g"

log_info "Maven环境变量: MAVEN_OPTS=$MAVEN_OPTS"

# 使用智能编译修复
log_info "使用智能编译修复..."

if [[ -f "/app/scripts/smart-compile.sh" ]]; then
    if /app/scripts/smart-compile.sh; then
        log_success "智能编译修复成功，继续正常流程"

        # 运行测试和生成报告
        log_info "运行测试和生成JaCoCo报告..."
        mvn test jacoco:report \
            -Dmaven.test.failure.ignore=true \
            -Dproject.build.sourceEncoding=UTF-8 \
            -Dmaven.compiler.source=11 \
            -Dmaven.compiler.target=11 \
            -Dmaven.resolver.transport=wagon \
            -Dmaven.wagon.http.retryHandler.count=3 \
            -Dmaven.wagon.http.pool=false \
            -U

        MAVEN_EXIT_CODE=$?
        log_info "Maven执行完成，返回码: $MAVEN_EXIT_CODE"
    else
        log_warning "智能编译修复失败，但可能已生成最小报告"
        MAVEN_EXIT_CODE=1
    fi
else
    log_warning "智能编译脚本不可用，使用传统方式"

    # 传统编译方式
    log_info "清理之前的构建..."
    mvn clean -q

    log_info "编译项目..."
    mvn compile -q || log_warning "项目编译失败"

    log_info "编译测试代码..."
    mvn test-compile -q || log_warning "测试代码编译失败"

    # 运行测试和生成报告
    log_info "运行测试和生成JaCoCo报告..."
    mvn test jacoco:report \
        -Dmaven.test.failure.ignore=true \
        -Dproject.build.sourceEncoding=UTF-8 \
        -Dmaven.compiler.source=11 \
        -Dmaven.compiler.target=11 \
        -Dmaven.resolver.transport=wagon \
        -Dmaven.wagon.http.retryHandler.count=3 \
        -Dmaven.wagon.http.pool=false \
        -U

    MAVEN_EXIT_CODE=$?
    log_info "Maven执行完成，返回码: $MAVEN_EXIT_CODE"
fi

# 检查target目录
log_info "检查target目录结构:"
if [[ -d "target" ]]; then
    find target -name "*.xml" -o -name "*.html" | head -20
else
    log_warning "target目录不存在"
fi

# 查找并复制JaCoCo报告
log_info "查找JaCoCo报告..."

# 可能的报告位置
POSSIBLE_LOCATIONS=(
    "target/site/jacoco/jacoco.xml"
    "target/jacoco-reports/jacoco.xml"
    "target/jacoco/jacoco.xml"
    "target/reports/jacoco/jacoco.xml"
)

JACOCO_XML=""
JACOCO_HTML_DIR=""

# 查找XML报告
for location in "${POSSIBLE_LOCATIONS[@]}"; do
    if [[ -f "$location" ]]; then
        JACOCO_XML="$location"
        JACOCO_HTML_DIR="$(dirname "$location")"
        log_success "找到JaCoCo XML报告: $location"
        break
    fi
done

# 如果还没找到，搜索整个target目录
if [[ -z "$JACOCO_XML" ]]; then
    log_info "在target目录中搜索JaCoCo报告..."
    FOUND_XML=$(find target -name "jacoco.xml" 2>/dev/null | head -1)
    if [[ -n "$FOUND_XML" ]]; then
        JACOCO_XML="$FOUND_XML"
        JACOCO_HTML_DIR="$(dirname "$FOUND_XML")"
        log_success "搜索到JaCoCo XML报告: $FOUND_XML"
    fi
fi

# 复制报告到输出目录
if [[ -n "$JACOCO_XML" && -f "$JACOCO_XML" ]]; then
    log_success "复制JaCoCo报告..."
    
    # 复制XML报告
    cp "$JACOCO_XML" "$REPORTS_DIR/"
    log_success "XML报告已复制到: $REPORTS_DIR/jacoco.xml"
    
    # 复制HTML报告目录
    if [[ -d "$JACOCO_HTML_DIR" ]]; then
        cp -r "$JACOCO_HTML_DIR" "$REPORTS_DIR/html"
        log_success "HTML报告已复制到: $REPORTS_DIR/html"
        
        # 列出HTML文件
        HTML_COUNT=$(find "$REPORTS_DIR/html" -name "*.html" | wc -l)
        log_info "复制了 $HTML_COUNT 个HTML文件"
    fi
    
    # 解析并显示覆盖率
    log_info "解析覆盖率数据..."
    python3 /app/scripts/parse-coverage.py "$REPORTS_DIR/jacoco.xml"
    
else
    log_error "未找到JaCoCo XML报告"
    log_info "可能的原因:"
    log_info "1. 项目没有测试代码"
    log_info "2. 测试执行失败"
    log_info "3. JaCoCo插件配置问题"
    
    # 创建空报告
    log_info "创建空的覆盖率报告..."
    cat > "$REPORTS_DIR/jacoco.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!DOCTYPE report PUBLIC "-//JACOCO//DTD Report 1.1//EN" "report.dtd">
<report name="Empty Report">
    <sessioninfo id="no-coverage" start="0" dump="0"/>
    <counter type="INSTRUCTION" missed="0" covered="0"/>
    <counter type="BRANCH" missed="0" covered="0"/>
    <counter type="LINE" missed="0" covered="0"/>
    <counter type="COMPLEXITY" missed="0" covered="0"/>
    <counter type="METHOD" missed="0" covered="0"/>
    <counter type="CLASS" missed="0" covered="0"/>
</report>
EOF
fi

# 生成摘要
log_info "生成覆盖率摘要..."
if [[ -f "/app/scripts/generate-summary.sh" ]]; then
    /app/scripts/generate-summary.sh "$REPORTS_DIR"
else
    log_warning "未找到 generate-summary.sh 脚本"
fi

# 复制日志文件
cp "$LOG_FILE" "$REPORTS_DIR/scan.log"

log_success "JaCoCo扫描完成"
log_info "报告位置: $REPORTS_DIR"
log_info "日志文件: $REPORTS_DIR/scan.log"

# 显示最终结果
if [[ -f "$REPORTS_DIR/jacoco.xml" ]]; then
    log_success "扫描成功完成"
    exit 0
else
    log_error "扫描失败"
    exit 1
fi
