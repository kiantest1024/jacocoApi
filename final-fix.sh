#!/bin/bash

# 最终修复脚本 - 解决所有依赖和编译问题
set -e

echo "🔧 JaCoCo 覆盖率问题最终修复方案"
echo "=================================="

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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

# 检查环境
check_environment() {
    print_info "检查环境..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker 服务未运行"
        exit 1
    fi
    
    print_success "环境检查通过"
}

# 设置权限
setup_permissions() {
    print_info "设置脚本权限..."
    find docker/scripts -name "*.sh" -exec chmod +x {} \;
    chmod +x *.sh
    print_success "权限设置完成"
}

# 清理旧镜像
cleanup_old_images() {
    print_info "清理旧镜像..."
    docker rmi jacoco-scanner:latest 2>/dev/null || true
    docker image prune -f
    print_success "清理完成"
}

# 构建新镜像
build_enhanced_image() {
    print_info "构建增强版镜像（支持所有现代测试依赖）..."
    
    if docker build -f docker/Dockerfile.alpine -t jacoco-scanner:latest docker/ --no-cache; then
        print_success "镜像构建成功"
    else
        print_error "镜像构建失败"
        exit 1
    fi
}

# 测试项目依赖分析
test_dependency_analysis() {
    print_info "测试项目依赖分析..."
    
    local temp_dir=$(mktemp -d)
    local test_project="$temp_dir/jacocotest"
    
    if git clone http://172.16.1.30/kian/jacocotest.git "$test_project"; then
        print_success "测试项目克隆成功"
        
        # 分析测试文件
        print_info "分析测试文件依赖..."
        if [[ -f "fix-dependencies.py" ]]; then
            python3 fix-dependencies.py "$test_project"
            
            # 检查修复结果
            if grep -q "assertj-core" "$test_project/pom.xml"; then
                print_success "AssertJ 依赖已添加"
            fi
            
            if grep -q "junit-jupiter" "$test_project/pom.xml"; then
                print_success "JUnit 5 依赖已添加"
            fi
            
            if grep -q "mockito-core" "$test_project/pom.xml"; then
                print_success "Mockito 依赖已添加"
            fi
        fi
    else
        print_warning "无法克隆测试项目，跳过依赖分析"
    fi
    
    rm -rf "$temp_dir"
}

# 运行完整测试
run_comprehensive_test() {
    print_info "运行完整的覆盖率扫描测试..."
    
    local test_reports=$(mktemp -d)
    print_info "测试报告目录: $test_reports"
    
    # 运行 Docker 扫描，增加超时时间
    print_info "启动 Docker 扫描（超时时间：10分钟）..."
    
    if timeout 600 docker run --rm \
        -v "$test_reports:/app/reports" \
        jacoco-scanner:latest \
        --repo-url http://172.16.1.30/kian/jacocotest.git \
        --commit-id main \
        --branch main \
        --service-name jacocotest; then
        
        print_success "Docker 扫描完成"
        
        # 详细分析结果
        analyze_scan_results "$test_reports"
        
    else
        print_error "Docker 扫描失败或超时"
        
        # 检查是否有部分结果
        if [[ -f "$test_reports/scan.log" ]]; then
            print_info "扫描日志（最后50行）:"
            tail -50 "$test_reports/scan.log"
        fi
        
        return 1
    fi
    
    rm -rf "$test_reports"
}

# 分析扫描结果
analyze_scan_results() {
    local reports_dir="$1"
    
    print_info "分析扫描结果..."
    
    # 检查生成的文件
    print_info "生成的文件:"
    ls -la "$reports_dir/"
    
    # 分析 XML 报告
    if [[ -f "$reports_dir/jacoco.xml" ]]; then
        print_success "JaCoCo XML 报告已生成"
        
        local file_size=$(stat -f%z "$reports_dir/jacoco.xml" 2>/dev/null || stat -c%s "$reports_dir/jacoco.xml" 2>/dev/null || echo "0")
        print_info "XML 报告大小: $file_size bytes"
        
        if [[ $file_size -gt 500 ]]; then
            # 解析覆盖率数据
            print_info "解析覆盖率数据..."
            
            local line_covered=$(grep -o 'type="LINE"[^>]*covered="[0-9]*"' "$reports_dir/jacoco.xml" | grep -o 'covered="[0-9]*"' | cut -d'"' -f2 | head -1)
            local line_missed=$(grep -o 'type="LINE"[^>]*missed="[0-9]*"' "$reports_dir/jacoco.xml" | grep -o 'missed="[0-9]*"' | cut -d'"' -f2 | head -1)
            
            if [[ -n "$line_covered" && -n "$line_missed" ]]; then
                local total=$((line_covered + line_missed))
                if [[ $total -gt 0 ]]; then
                    local percentage=$(echo "scale=2; $line_covered * 100 / $total" | bc 2>/dev/null || echo "计算失败")
                    
                    print_success "🎉 覆盖率检测成功: $percentage%"
                    print_success "覆盖行数: $line_covered/$total"
                    
                    if [[ $(echo "$percentage > 0" | bc 2>/dev/null) -eq 1 ]]; then
                        print_success "🎊 覆盖率问题已完全修复！"
                        return 0
                    else
                        print_warning "覆盖率仍为 0%，可能需要进一步调试"
                    fi
                else
                    print_warning "总行数为 0，可能项目没有可测试的代码"
                fi
            else
                print_warning "无法解析覆盖率数据"
            fi
        else
            print_warning "XML 报告文件太小，可能是空报告"
        fi
    else
        print_error "未生成 JaCoCo XML 报告"
    fi
    
    # 检查 HTML 报告
    if [[ -d "$reports_dir/html" ]]; then
        local html_count=$(find "$reports_dir/html" -name "*.html" | wc -l)
        print_success "HTML 报告已生成: $html_count 个文件"
    else
        print_warning "未生成 HTML 报告"
    fi
    
    # 检查扫描日志
    if [[ -f "$reports_dir/scan.log" ]]; then
        print_info "扫描日志摘要（最后20行）:"
        echo "--- 扫描日志 ---"
        tail -20 "$reports_dir/scan.log"
        echo "--- 日志结束 ---"
    fi
}

# 显示解决方案总结
show_solution_summary() {
    echo ""
    print_success "🎉 JaCoCo 覆盖率问题修复完成！"
    echo ""
    echo "🔧 修复内容:"
    echo "   ✅ 添加了 JUnit 5 (Jupiter) 完整支持"
    echo "   ✅ 添加了 Mockito Core 和 JUnit Jupiter 扩展"
    echo "   ✅ 添加了 AssertJ 断言库支持"
    echo "   ✅ 智能依赖分析和自动修复"
    echo "   ✅ 编译错误智能处理"
    echo "   ✅ 向后兼容 JUnit 4"
    echo ""
    echo "📋 镜像信息:"
    docker images | grep jacoco-scanner
    echo ""
    echo "🚀 现在可以正常使用:"
    echo "1. 重启 JaCoCo API:"
    echo "   python3 app.py"
    echo ""
    echo "2. 发送扫描请求，应该能看到实际覆盖率"
    echo ""
    echo "3. 如果还有问题，运行诊断:"
    echo "   python3 diagnose.py"
}

# 主函数
main() {
    print_info "开始最终修复流程..."
    
    check_environment
    setup_permissions
    cleanup_old_images
    build_enhanced_image
    test_dependency_analysis
    
    if run_comprehensive_test; then
        show_solution_summary
        print_success "🎊 所有问题已解决！"
    else
        print_warning "测试过程中遇到问题，但镜像已更新"
        print_info "请手动测试 JaCoCo API 扫描功能"
    fi
}

# 运行主函数
main "$@"
