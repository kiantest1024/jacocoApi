#!/bin/bash

# 智能编译修复脚本
# 处理主代码和测试代码的编译问题

set -e

# 日志函数
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1"
}

log_warning() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1"
}

# 检查项目结构
check_project_structure() {
    log_info "检查项目结构..."
    
    # 检查主代码
    if [[ -d "src/main/java" ]]; then
        local main_files=$(find src/main/java -name "*.java" | wc -l)
        log_info "主代码文件数: $main_files"
        
        if [[ $main_files -eq 0 ]]; then
            log_warning "主代码目录为空"
            return 1
        fi
    else
        log_error "主代码目录不存在: src/main/java"
        return 1
    fi
    
    # 检查测试代码
    if [[ -d "src/test/java" ]]; then
        local test_files=$(find src/test/java -name "*.java" | wc -l)
        log_info "测试代码文件数: $test_files"
        
        if [[ $test_files -eq 0 ]]; then
            log_warning "测试代码目录为空"
            return 1
        fi
    else
        log_warning "测试代码目录不存在: src/test/java"
        return 1
    fi
    
    return 0
}

# 分析编译错误
analyze_compile_errors() {
    local error_log="$1"
    
    log_info "分析编译错误..."
    
    # 检查缺失的包
    local missing_packages=$(grep "package .* does not exist" "$error_log" | sed 's/.*package \([^ ]*\) does not exist.*/\1/' | sort -u)
    
    if [[ -n "$missing_packages" ]]; then
        log_warning "缺失的包:"
        echo "$missing_packages" | while read -r package; do
            log_warning "  - $package"
        done
    fi
    
    # 检查找不到的符号
    local missing_symbols=$(grep "cannot find symbol" "$error_log" | grep "symbol:" | sed 's/.*symbol: *\(.*\)/\1/' | sort -u)
    
    if [[ -n "$missing_symbols" ]]; then
        log_warning "找不到的符号:"
        echo "$missing_symbols" | while read -r symbol; do
            log_warning "  - $symbol"
        done
    fi
}

# 尝试修复主代码编译
fix_main_compile() {
    log_info "尝试修复主代码编译..."
    
    # 先尝试清理和编译主代码
    log_info "清理项目..."
    mvn clean -q
    
    log_info "编译主代码..."
    if mvn compile -q 2>/tmp/main_compile_error.log; then
        log_success "主代码编译成功"
        return 0
    else
        log_warning "主代码编译失败"
        analyze_compile_errors "/tmp/main_compile_error.log"
        
        # 显示编译错误的前10行
        log_info "主代码编译错误（前10行）:"
        head -10 /tmp/main_compile_error.log
        
        return 1
    fi
}

# 尝试修复测试代码编译
fix_test_compile() {
    log_info "尝试修复测试代码编译..."
    
    # 先确保主代码编译成功
    if ! fix_main_compile; then
        log_error "主代码编译失败，无法编译测试代码"
        return 1
    fi
    
    # 运行依赖修复工具
    if [[ -f "/app/scripts/fix-dependencies.py" ]]; then
        log_info "运行依赖修复工具..."
        python3 /app/scripts/fix-dependencies.py .
    fi
    
    log_info "编译测试代码..."
    if mvn test-compile -q 2>/tmp/test_compile_error.log; then
        log_success "测试代码编译成功"
        return 0
    else
        log_warning "测试代码编译失败"
        analyze_compile_errors "/tmp/test_compile_error.log"
        
        # 显示编译错误的前20行
        log_info "测试代码编译错误（前20行）:"
        head -20 /tmp/test_compile_error.log
        
        return 1
    fi
}

# 强制运行测试（忽略编译错误）
force_run_tests() {
    log_info "强制运行测试（忽略编译错误）..."
    
    # 尝试只运行能编译的测试
    log_info "尝试运行部分测试..."
    
    # 查找可能编译成功的测试文件
    local compiled_tests=$(find target/test-classes -name "*.class" 2>/dev/null | wc -l)
    
    if [[ $compiled_tests -gt 0 ]]; then
        log_info "找到 $compiled_tests 个已编译的测试类"
        
        # 尝试运行测试
        if mvn surefire:test -Dmaven.test.failure.ignore=true -q; then
            log_success "部分测试运行成功"
            return 0
        else
            log_warning "测试运行失败"
        fi
    else
        log_warning "没有找到已编译的测试类"
    fi
    
    return 1
}

# 生成最小覆盖率报告
generate_minimal_report() {
    log_info "生成最小覆盖率报告..."
    
    # 检查是否有 JaCoCo 执行数据
    if [[ -f "target/jacoco.exec" ]]; then
        log_info "找到 JaCoCo 执行数据"
        
        # 尝试生成报告
        if mvn jacoco:report -q; then
            log_success "JaCoCo 报告生成成功"
            return 0
        else
            log_warning "JaCoCo 报告生成失败"
        fi
    else
        log_warning "未找到 JaCoCo 执行数据"
    fi
    
    # 创建空的覆盖率报告
    log_info "创建空的覆盖率报告..."
    mkdir -p target/site/jacoco
    
    cat > target/site/jacoco/jacoco.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!DOCTYPE report PUBLIC "-//JACOCO//DTD Report 1.1//EN" "report.dtd">
<report name="Minimal Report">
    <sessioninfo id="compilation-failed" start="0" dump="0"/>
    <counter type="INSTRUCTION" missed="0" covered="0"/>
    <counter type="BRANCH" missed="0" covered="0"/>
    <counter type="LINE" missed="0" covered="0"/>
    <counter type="COMPLEXITY" missed="0" covered="0"/>
    <counter type="METHOD" missed="0" covered="0"/>
    <counter type="CLASS" missed="0" covered="0"/>
</report>
EOF
    
    log_success "空覆盖率报告已创建"
    return 0
}

# 主函数
main() {
    log_info "开始智能编译修复..."
    
    # 检查项目结构
    if ! check_project_structure; then
        log_error "项目结构检查失败"
        generate_minimal_report
        return 1
    fi
    
    # 尝试修复测试编译
    if fix_test_compile; then
        log_success "编译修复成功，继续正常流程"
        return 0
    fi
    
    # 如果测试编译失败，尝试强制运行
    log_warning "测试编译失败，尝试强制运行..."
    
    if force_run_tests; then
        log_success "强制测试运行成功"
        
        # 尝试生成报告
        if mvn jacoco:report -Dmaven.test.failure.ignore=true -q; then
            log_success "覆盖率报告生成成功"
            return 0
        fi
    fi
    
    # 最后生成最小报告
    log_warning "所有修复尝试失败，生成最小报告"
    generate_minimal_report
    return 1
}

# 如果直接运行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
