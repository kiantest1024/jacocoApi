#!/bin/bash

# 重新构建支持现代测试依赖的 JaCoCo Scanner
set -e

echo "🚀 重新构建支持 JUnit 5 + Mockito 的 JaCoCo Scanner..."

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

# 检查Docker环境
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装或不可用"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker 服务未运行"
        exit 1
    fi
    
    print_success "Docker 环境检查通过"
}

# 确保所有脚本有执行权限
setup_permissions() {
    print_info "设置脚本权限..."
    chmod +x docker/scripts/*.sh
    chmod +x *.sh
    print_success "权限设置完成"
}

# 清理旧镜像
cleanup_old() {
    print_info "清理旧镜像..."
    docker rmi jacoco-scanner:latest 2>/dev/null || true
    docker image prune -f
    print_success "清理完成"
}

# 构建新镜像
build_image() {
    print_info "构建新镜像（支持 JUnit 5 + Mockito）..."
    
    if docker build -f docker/Dockerfile.alpine -t jacoco-scanner:latest docker/ --no-cache; then
        print_success "镜像构建成功"
    else
        print_error "镜像构建失败"
        exit 1
    fi
}

# 测试依赖修复功能
test_dependency_fix() {
    print_info "测试依赖修复功能..."
    
    # 创建临时测试项目
    local temp_dir=$(mktemp -d)
    local test_project="$temp_dir/test_project"
    
    # 克隆测试项目
    if git clone http://172.16.1.30/kian/jacocotest.git "$test_project"; then
        print_success "测试项目克隆成功"
        
        # 分析项目依赖
        print_info "分析项目依赖需求..."
        if [[ -f "fix-dependencies.py" ]]; then
            python3 fix-dependencies.py "$test_project"
        fi
        
        # 检查修复后的 pom.xml
        if grep -q "junit-jupiter" "$test_project/pom.xml"; then
            print_success "检测到 JUnit 5 依赖"
        fi
        
        if grep -q "mockito-core" "$test_project/pom.xml"; then
            print_success "检测到 Mockito 依赖"
        fi
        
    else
        print_warning "无法克隆测试项目，跳过依赖测试"
    fi
    
    # 清理
    rm -rf "$temp_dir"
}

# 运行完整测试
run_full_test() {
    print_info "运行完整的 Docker 扫描测试..."
    
    local test_reports=$(mktemp -d)
    
    print_info "测试报告目录: $test_reports"
    
    # 运行 Docker 扫描
    if timeout 600 docker run --rm \
        -v "$test_reports:/app/reports" \
        jacoco-scanner:latest \
        --repo-url http://172.16.1.30/kian/jacocotest.git \
        --commit-id main \
        --branch main \
        --service-name jacocotest; then
        
        print_success "Docker 扫描完成"
        
        # 检查结果
        if [[ -f "$test_reports/jacoco.xml" ]]; then
            print_success "生成了 JaCoCo XML 报告"
            
            # 检查覆盖率
            local line_covered=$(grep -o 'type="LINE"[^>]*covered="[0-9]*"' "$test_reports/jacoco.xml" | grep -o 'covered="[0-9]*"' | cut -d'"' -f2 | head -1)
            local line_missed=$(grep -o 'type="LINE"[^>]*missed="[0-9]*"' "$test_reports/jacoco.xml" | grep -o 'missed="[0-9]*"' | cut -d'"' -f2 | head -1)
            
            if [[ -n "$line_covered" && -n "$line_missed" ]]; then
                local total=$((line_covered + line_missed))
                if [[ $total -gt 0 ]]; then
                    local percentage=$(echo "scale=2; $line_covered * 100 / $total" | bc 2>/dev/null || echo "计算失败")
                    print_success "检测到覆盖率: $percentage% (覆盖 $line_covered/$total 行)"
                    
                    if [[ $(echo "$percentage > 0" | bc 2>/dev/null) -eq 1 ]]; then
                        print_success "🎉 覆盖率问题已修复！"
                    else
                        print_warning "覆盖率仍为 0%，可能需要进一步调试"
                    fi
                else
                    print_warning "总行数为 0"
                fi
            else
                print_warning "无法解析覆盖率数据"
            fi
        else
            print_error "未生成 JaCoCo XML 报告"
        fi
        
        # 检查扫描日志
        if [[ -f "$test_reports/scan.log" ]]; then
            print_info "扫描日志摘要:"
            echo "--- 最后 20 行日志 ---"
            tail -20 "$test_reports/scan.log"
            echo "--- 日志结束 ---"
        fi
        
    else
        print_error "Docker 扫描失败或超时"
        return 1
    fi
    
    # 清理
    rm -rf "$test_reports"
}

# 显示使用说明
show_usage() {
    echo ""
    print_success "🎉 支持现代测试依赖的 JaCoCo Scanner 构建完成！"
    echo ""
    echo "🔧 新功能:"
    echo "   ✅ 自动检测 JUnit 5 (Jupiter) 依赖"
    echo "   ✅ 自动添加 Mockito 支持"
    echo "   ✅ 智能依赖修复"
    echo "   ✅ 向后兼容 JUnit 4"
    echo "   ✅ Maven Surefire 插件配置"
    echo ""
    echo "📋 镜像信息:"
    docker images | grep jacoco-scanner
    echo ""
    echo "🚀 使用方法:"
    echo "1. 重新运行 JaCoCo API:"
    echo "   python3 app.py"
    echo ""
    echo "2. 测试扫描:"
    echo "   ./test-coverage.sh"
    echo ""
    echo "3. 手动测试:"
    echo "   docker run --rm -v \"\$(pwd)/test_reports:/app/reports\" jacoco-scanner:latest \\"
    echo "     --repo-url http://172.16.1.30/kian/jacocotest.git \\"
    echo "     --commit-id main --branch main --service-name jacocotest"
}

# 主函数
main() {
    echo "🔧 构建支持现代测试依赖的 JaCoCo Scanner"
    echo "=========================================="
    
    check_docker
    setup_permissions
    cleanup_old
    build_image
    test_dependency_fix
    run_full_test
    show_usage
    
    print_success "所有操作完成！现在应该能正确处理 JUnit 5 + Mockito 项目了。"
}

# 运行主函数
main "$@"
