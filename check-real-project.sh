#!/bin/bash

# 检查真实项目的具体问题
set -e

echo "🔍 检查真实项目 jacocotest 的具体问题"
echo "===================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}💡 $1${NC}"; }

REPO_URL="http://172.16.1.30/kian/jacocotest.git"
TEMP_DIR=$(mktemp -d)
PROJECT_DIR="$TEMP_DIR/jacocotest"

# 清理函数
cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# 克隆项目
clone_and_analyze() {
    print_info "克隆并分析真实项目..."
    
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    print_success "项目克隆成功"
}

# 深度分析测试文件
analyze_test_execution() {
    print_info "深度分析测试执行..."
    
    # 查看测试文件的具体内容
    local test_file="src/test/java/com/login/Main_main.java"
    
    if [[ -f "$test_file" ]]; then
        print_info "分析测试文件: $test_file"
        
        echo "📄 测试文件前50行:"
        head -50 "$test_file"
        
        echo ""
        echo "🔍 测试方法分析:"
        grep -n "@Test\|@ParameterizedTest\|@RepeatedTest" "$test_file" || print_warning "未找到测试注解"
        
        echo ""
        echo "🔍 主代码调用分析:"
        grep -n "new \|\..*(" "$test_file" | head -10 || print_warning "未找到明显的主代码调用"
        
        echo ""
        echo "🔍 断言分析:"
        grep -n "assert\|verify\|expect" "$test_file" | head -10 || print_warning "未找到断言语句"
    fi
}

# 检查主代码结构
analyze_main_code() {
    print_info "分析主代码结构..."
    
    if [[ -d "src/main/java" ]]; then
        echo "📁 主代码文件:"
        find src/main/java -name "*.java" | while read -r file; do
            echo "  $file"
            echo "    类定义: $(grep -n "^public class\|^class" "$file" || echo "未找到类定义")"
            echo "    方法数: $(grep -c "public.*(" "$file" || echo "0")"
        done
    else
        print_warning "主代码目录不存在"
    fi
}

# 手动运行单个测试方法
run_single_test() {
    print_info "尝试运行单个测试方法..."
    
    # 先编译
    mvn clean compile test-compile -q
    
    # 尝试运行特定的测试类
    local test_class="com.login.MainTest"
    
    print_info "运行测试类: $test_class"
    mvn test -Dtest="$test_class" -Dmaven.test.failure.ignore=true
    
    # 检查结果
    if [[ -d "target/surefire-reports" ]]; then
        echo "📊 测试结果:"
        ls -la target/surefire-reports/
        
        # 查看具体的测试报告
        local report_file="target/surefire-reports/TEST-${test_class}.xml"
        if [[ -f "$report_file" ]]; then
            echo "📄 测试报告内容:"
            cat "$report_file"
        fi
    fi
}

# 检查 JaCoCo 配置
check_jacoco_config() {
    print_info "检查 JaCoCo 配置..."
    
    echo "📄 pom.xml 中的 JaCoCo 配置:"
    grep -A 20 -B 5 "jacoco" pom.xml || print_warning "pom.xml 中未找到 JaCoCo 配置"
    
    echo ""
    echo "📄 Maven 插件列表:"
    grep -A 5 "<plugin>" pom.xml | grep -E "groupId|artifactId" || print_warning "未找到插件配置"
}

# 强制运行 JaCoCo
force_jacoco_run() {
    print_info "强制运行 JaCoCo..."
    
    # 清理
    mvn clean -q
    
    # 显式运行 JaCoCo prepare-agent
    print_info "运行 JaCoCo prepare-agent..."
    mvn jacoco:prepare-agent -X > jacoco_prepare.log 2>&1
    
    echo "JaCoCo prepare-agent 日志:"
    tail -20 jacoco_prepare.log
    
    # 编译
    mvn compile test-compile -q
    
    # 运行测试
    print_info "运行测试..."
    mvn surefire:test -Dmaven.test.failure.ignore=true
    
    # 检查 jacoco.exec
    if [[ -f "target/jacoco.exec" ]]; then
        local size=$(stat -f%z "target/jacoco.exec" 2>/dev/null || stat -c%s "target/jacoco.exec" 2>/dev/null || echo "0")
        print_info "JaCoCo 执行文件大小: $size bytes"
        
        if [[ $size -gt 0 ]]; then
            print_success "JaCoCo 收集到了执行数据"
        else
            print_warning "JaCoCo 执行文件为空"
        fi
    else
        print_error "JaCoCo 执行文件不存在"
    fi
    
    # 生成报告
    print_info "生成 JaCoCo 报告..."
    mvn jacoco:report -X > jacoco_report.log 2>&1
    
    echo "JaCoCo 报告生成日志:"
    tail -20 jacoco_report.log
    
    # 检查报告
    if [[ -f "target/site/jacoco/jacoco.xml" ]]; then
        print_success "JaCoCo XML 报告已生成"
        
        echo "📊 报告内容:"
        cat target/site/jacoco/jacoco.xml
        
    else
        print_error "JaCoCo XML 报告未生成"
    fi
}

# 检查测试是否真正执行了主代码
check_test_main_interaction() {
    print_info "检查测试与主代码的交互..."
    
    # 在主代码中添加调试输出
    local main_files=$(find src/main/java -name "*.java")
    
    for main_file in $main_files; do
        if [[ -f "$main_file" ]]; then
            echo "📄 主代码文件: $main_file"
            echo "方法列表:"
            grep -n "public.*(" "$main_file" | head -5
        fi
    done
    
    # 检查测试是否调用了这些方法
    local test_files=$(find src/test/java -name "*.java")
    
    for test_file in $test_files; do
        if [[ -f "$test_file" ]]; then
            echo "📄 测试文件: $test_file"
            echo "可能的主代码调用:"
            grep -n "new \|Main\|Database\|Login" "$test_file" | head -10 || echo "未找到明显的主代码调用"
        fi
    done
}

# 创建诊断报告
create_diagnosis_report() {
    print_info "创建诊断报告..."
    
    cat > diagnosis_report.md << EOF
# JaCoCo 覆盖率为 0% 诊断报告

## 项目信息
- 仓库: $REPO_URL
- 分析时间: $(date)

## 发现的问题

### 1. 项目结构
$(if [[ -d "src/main/java" ]]; then echo "✅ 主代码目录存在"; else echo "❌ 主代码目录不存在"; fi)
$(if [[ -d "src/test/java" ]]; then echo "✅ 测试代码目录存在"; else echo "❌ 测试代码目录不存在"; fi)

### 2. 编译状态
$(if mvn compile -q 2>/dev/null; then echo "✅ 主代码编译成功"; else echo "❌ 主代码编译失败"; fi)
$(if mvn test-compile -q 2>/dev/null; then echo "✅ 测试代码编译成功"; else echo "❌ 测试代码编译失败"; fi)

### 3. 测试执行
$(if [[ -d "target/surefire-reports" ]] && [[ -n "$(ls target/surefire-reports/ 2>/dev/null)" ]]; then echo "✅ 测试报告已生成"; else echo "❌ 测试报告未生成"; fi)

### 4. JaCoCo 数据收集
$(if [[ -f "target/jacoco.exec" ]] && [[ $(stat -f%z "target/jacoco.exec" 2>/dev/null || stat -c%s "target/jacoco.exec" 2>/dev/null || echo "0") -gt 0 ]]; then echo "✅ JaCoCo 收集到数据"; else echo "❌ JaCoCo 未收集到数据"; fi)

### 5. 覆盖率报告
$(if [[ -f "target/site/jacoco/jacoco.xml" ]]; then echo "✅ JaCoCo 报告已生成"; else echo "❌ JaCoCo 报告未生成"; fi)

## 建议的修复步骤

1. 确保所有依赖都已正确添加
2. 验证测试方法确实调用了主代码
3. 检查 JaCoCo 插件配置
4. 确认测试执行过程中没有跳过

## 详细日志文件
- jacoco_prepare.log: JaCoCo prepare-agent 日志
- jacoco_report.log: JaCoCo 报告生成日志
EOF

    print_success "诊断报告已保存到 diagnosis_report.md"
}

# 主函数
main() {
    clone_and_analyze
    analyze_test_execution
    analyze_main_code
    check_jacoco_config
    run_single_test
    force_jacoco_run
    check_test_main_interaction
    create_diagnosis_report
    
    print_info "诊断完成"
    
    # 询问是否保留诊断文件
    echo ""
    read -p "是否保留诊断文件到当前目录？(y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp -r "$PROJECT_DIR" ./real_project_debug
        print_success "诊断文件已保存到 ./real_project_debug"
    fi
}

# 运行主函数
main "$@"
