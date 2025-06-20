#!/bin/bash

# JaCoCo 覆盖率深度调试脚本
set -e

echo "🔍 JaCoCo 覆盖率深度调试工具"
echo "============================="

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

# 测试项目URL
REPO_URL="http://172.16.1.30/kian/jacocotest.git"
TEMP_DIR=$(mktemp -d)
PROJECT_DIR="$TEMP_DIR/jacocotest"

print_info "临时目录: $TEMP_DIR"

# 清理函数
cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# 克隆项目
clone_project() {
    print_info "克隆测试项目..."
    
    if git clone "$REPO_URL" "$PROJECT_DIR"; then
        print_success "项目克隆成功"
        cd "$PROJECT_DIR"
    else
        print_error "项目克隆失败"
        exit 1
    fi
}

# 分析项目结构
analyze_project() {
    print_info "分析项目结构..."
    
    echo "📁 项目根目录:"
    ls -la
    
    echo ""
    echo "📁 源代码结构:"
    if [[ -d "src" ]]; then
        find src -type f -name "*.java" | head -20
    else
        print_warning "src 目录不存在"
    fi
    
    echo ""
    echo "📄 pom.xml 内容（前50行）:"
    head -50 pom.xml
}

# 检查测试文件内容
analyze_test_files() {
    print_info "分析测试文件..."
    
    if [[ -d "src/test/java" ]]; then
        local test_files=$(find src/test/java -name "*.java")
        
        echo "🧪 测试文件列表:"
        echo "$test_files"
        
        echo ""
        echo "🔍 测试文件内容分析:"
        for test_file in $test_files; do
            echo "--- $test_file ---"
            echo "导入语句:"
            grep "^import" "$test_file" | head -10
            echo ""
            echo "测试方法:"
            grep -n "@Test\|@ParameterizedTest\|@RepeatedTest" "$test_file" || echo "未找到测试方法"
            echo ""
            echo "断言语句:"
            grep -n "assert\|verify\|when\|given" "$test_file" | head -5 || echo "未找到断言"
            echo "========================"
        done
    else
        print_warning "测试目录不存在"
    fi
}

# 手动运行 Maven 测试
run_manual_test() {
    print_info "手动运行 Maven 测试..."
    
    # 清理
    print_info "清理项目..."
    mvn clean -q
    
    # 编译主代码
    print_info "编译主代码..."
    if mvn compile; then
        print_success "主代码编译成功"
    else
        print_error "主代码编译失败"
        return 1
    fi
    
    # 编译测试代码
    print_info "编译测试代码..."
    if mvn test-compile; then
        print_success "测试代码编译成功"
    else
        print_error "测试代码编译失败"
        return 1
    fi
    
    # 检查编译后的类
    print_info "检查编译后的类文件..."
    echo "主代码类:"
    find target/classes -name "*.class" 2>/dev/null | head -10 || echo "无主代码类"
    echo ""
    echo "测试代码类:"
    find target/test-classes -name "*.class" 2>/dev/null | head -10 || echo "无测试代码类"
    
    # 运行测试（不使用 JaCoCo）
    print_info "运行测试（不使用 JaCoCo）..."
    mvn surefire:test -Dmaven.test.failure.ignore=true
    
    # 检查测试结果
    if [[ -d "target/surefire-reports" ]]; then
        print_info "测试报告:"
        ls -la target/surefire-reports/
        
        # 显示测试结果摘要
        if [[ -f "target/surefire-reports/TEST-*.xml" ]]; then
            local test_files=(target/surefire-reports/TEST-*.xml)
            for test_file in "${test_files[@]}"; do
                if [[ -f "$test_file" ]]; then
                    echo "--- $(basename "$test_file") ---"
                    grep -o 'tests="[0-9]*"' "$test_file" || echo "无测试数据"
                    grep -o 'failures="[0-9]*"' "$test_file" || echo "无失败数据"
                    grep -o 'errors="[0-9]*"' "$test_file" || echo "无错误数据"
                fi
            done
        fi
    else
        print_warning "未生成测试报告"
    fi
}

# 运行带 JaCoCo 的测试
run_jacoco_test() {
    print_info "运行带 JaCoCo 的测试..."
    
    # 清理
    mvn clean -q
    
    # 运行带 JaCoCo 的测试
    print_info "执行 JaCoCo 测试..."
    mvn test jacoco:report -Dmaven.test.failure.ignore=true -X > jacoco_debug.log 2>&1
    
    # 检查 JaCoCo 执行数据
    print_info "检查 JaCoCo 执行数据..."
    if [[ -f "target/jacoco.exec" ]]; then
        local exec_size=$(stat -f%z "target/jacoco.exec" 2>/dev/null || stat -c%s "target/jacoco.exec" 2>/dev/null || echo "0")
        print_success "JaCoCo 执行数据文件存在，大小: $exec_size bytes"
        
        if [[ $exec_size -gt 0 ]]; then
            print_success "JaCoCo 执行数据不为空"
        else
            print_warning "JaCoCo 执行数据为空"
        fi
    else
        print_error "JaCoCo 执行数据文件不存在"
    fi
    
    # 检查 JaCoCo 报告
    print_info "检查 JaCoCo 报告..."
    if [[ -f "target/site/jacoco/jacoco.xml" ]]; then
        print_success "JaCoCo XML 报告存在"
        
        echo "XML 报告内容（前20行）:"
        head -20 target/site/jacoco/jacoco.xml
        
        echo ""
        echo "覆盖率计数器:"
        grep "<counter" target/site/jacoco/jacoco.xml || echo "未找到计数器"
        
    else
        print_error "JaCoCo XML 报告不存在"
    fi
    
    # 显示 Maven 调试日志的关键部分
    print_info "Maven 调试日志关键信息:"
    echo "JaCoCo 相关日志:"
    grep -i jacoco jacoco_debug.log | head -20 || echo "无 JaCoCo 日志"
    
    echo ""
    echo "测试执行日志:"
    grep -i "running\|test" jacoco_debug.log | head -10 || echo "无测试执行日志"
}

# 分析为什么覆盖率为 0
analyze_zero_coverage() {
    print_info "分析覆盖率为 0 的原因..."
    
    local reasons=()
    
    # 检查是否有测试执行
    if [[ ! -d "target/surefire-reports" ]] || [[ -z "$(ls target/surefire-reports/ 2>/dev/null)" ]]; then
        reasons+=("测试没有执行")
    fi
    
    # 检查 JaCoCo 代理
    if [[ ! -f "target/jacoco.exec" ]] || [[ $(stat -f%z "target/jacoco.exec" 2>/dev/null || stat -c%s "target/jacoco.exec" 2>/dev/null || echo "0") -eq 0 ]]; then
        reasons+=("JaCoCo 代理没有收集数据")
    fi
    
    # 检查主代码类
    local main_classes=$(find target/classes -name "*.class" 2>/dev/null | wc -l)
    if [[ $main_classes -eq 0 ]]; then
        reasons+=("主代码没有编译成功")
    fi
    
    # 检查测试类
    local test_classes=$(find target/test-classes -name "*.class" 2>/dev/null | wc -l)
    if [[ $test_classes -eq 0 ]]; then
        reasons+=("测试代码没有编译成功")
    fi
    
    # 检查测试是否真正运行了主代码
    if grep -q "No tests were executed" jacoco_debug.log 2>/dev/null; then
        reasons+=("没有测试被执行")
    fi
    
    echo "🔍 可能的原因:"
    for reason in "${reasons[@]}"; do
        print_warning "$reason"
    done
    
    # 提供解决建议
    echo ""
    echo "💡 解决建议:"
    
    if [[ ${#reasons[@]} -eq 0 ]]; then
        print_info "所有检查都通过，可能是测试没有覆盖主代码"
        print_info "建议检查测试是否真正调用了主代码的方法"
    else
        for reason in "${reasons[@]}"; do
            case "$reason" in
                *"测试没有执行"*)
                    print_info "确保测试方法有 @Test 注解且能被 Maven Surefire 发现"
                    ;;
                *"JaCoCo 代理"*)
                    print_info "检查 JaCoCo 插件配置，确保 prepare-agent 目标执行"
                    ;;
                *"主代码没有编译"*)
                    print_info "修复主代码编译错误"
                    ;;
                *"测试代码没有编译"*)
                    print_info "修复测试代码编译错误，添加缺失依赖"
                    ;;
            esac
        done
    fi
}

# 创建修复建议
create_fix_suggestions() {
    print_info "生成修复建议..."
    
    cat > coverage_fix_suggestions.md << 'EOF'
# JaCoCo 覆盖率为 0% 修复建议

## 检查清单

### 1. 测试执行检查
- [ ] 测试方法有正确的 @Test 注解
- [ ] 测试类名以 Test 结尾或以 Test 开头
- [ ] 测试方法是 public void
- [ ] 没有编译错误

### 2. JaCoCo 配置检查
- [ ] pom.xml 包含 jacoco-maven-plugin
- [ ] prepare-agent 目标在测试前执行
- [ ] 没有排除主代码包

### 3. 代码覆盖检查
- [ ] 测试真正调用了主代码方法
- [ ] 主代码类在 src/main/java 下
- [ ] 测试代码在 src/test/java 下

### 4. Maven 配置检查
- [ ] Surefire 插件版本支持 JUnit 5
- [ ] 所有必要依赖都已添加
- [ ] 没有测试跳过配置

## 手动验证步骤

1. 运行单独的测试：
   ```bash
   mvn test -Dtest=YourTestClass
   ```

2. 检查测试是否真正执行：
   ```bash
   mvn test -Dmaven.test.failure.ignore=true
   ls target/surefire-reports/
   ```

3. 验证 JaCoCo 数据收集：
   ```bash
   mvn clean test jacoco:report
   ls -la target/jacoco.exec
   ```

4. 检查主代码是否被调用：
   在测试中添加 System.out.println 验证
EOF

    print_success "修复建议已保存到 coverage_fix_suggestions.md"
}

# 主函数
main() {
    clone_project
    analyze_project
    analyze_test_files
    run_manual_test
    run_jacoco_test
    analyze_zero_coverage
    create_fix_suggestions
    
    print_info "调试完成，请查看生成的日志和建议文件"
    print_info "临时目录: $TEMP_DIR (退出时自动清理)"
    
    # 询问是否保留调试文件
    echo ""
    read -p "是否保留调试文件到当前目录？(y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp -r "$PROJECT_DIR" ./debug_project
        cp "$PROJECT_DIR/jacoco_debug.log" ./jacoco_debug.log 2>/dev/null || true
        cp "$PROJECT_DIR/coverage_fix_suggestions.md" ./coverage_fix_suggestions.md 2>/dev/null || true
        print_success "调试文件已保存到当前目录"
    fi
}

# 运行主函数
main "$@"
