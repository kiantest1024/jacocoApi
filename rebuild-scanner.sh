#!/bin/bash

# 重新构建增强版 JaCoCo Scanner Docker 镜像
set -e

echo "🚀 重新构建增强版 JaCoCo Scanner Docker 镜像..."

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
        print_info "启动命令: sudo systemctl start docker"
        exit 1
    fi
    
    print_success "Docker 环境检查通过"
}

# 检查必要文件
check_files() {
    local required_files=(
        "docker/Dockerfile.alpine"
        "docker/scripts/scan-enhanced.sh"
        "docker/scripts/parse-coverage.py"
        "docker/scripts/generate-summary.sh"
        "docker/scripts/settings.xml"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            print_error "缺少必要文件: $file"
            exit 1
        fi
    done
    
    print_success "必要文件检查通过"
}

# 清理旧镜像
cleanup_old_images() {
    echo "🧹 清理旧镜像..."
    
    # 删除旧的jacoco-scanner镜像
    if docker images | grep -q "jacoco-scanner"; then
        print_info "删除旧的 jacoco-scanner 镜像..."
        docker rmi jacoco-scanner:latest 2>/dev/null || true
        docker image prune -f
    fi
    
    print_success "旧镜像清理完成"
}

# 构建新镜像
build_image() {
    echo "🔨 构建新的增强版镜像..."
    
    # 确保脚本有执行权限
    chmod +x docker/scripts/*.sh
    
    # 构建镜像
    if docker build -f docker/Dockerfile.alpine -t jacoco-scanner:latest docker/ --no-cache; then
        print_success "镜像构建成功"
    else
        print_error "镜像构建失败"
        exit 1
    fi
}

# 测试镜像
test_image() {
    echo "🧪 测试新镜像..."
    
    # 创建临时目录用于测试
    local temp_reports=$(mktemp -d)
    
    print_info "测试目录: $temp_reports"
    
    # 运行测试扫描
    print_info "运行测试扫描..."
    if docker run --rm \
        -v "$temp_reports:/app/reports" \
        jacoco-scanner:latest \
        --repo-url http://172.16.1.30/kian/jacocotest.git \
        --commit-id main \
        --branch main \
        --service-name jacocotest; then
        
        print_success "Docker 扫描测试成功"
        
        # 检查生成的文件
        echo "📋 生成的文件:"
        ls -la "$temp_reports/"
        
        if [[ -f "$temp_reports/jacoco.xml" ]]; then
            print_success "生成了 JaCoCo XML 报告"
            
            # 显示文件大小
            local xml_size=$(stat -f%z "$temp_reports/jacoco.xml" 2>/dev/null || stat -c%s "$temp_reports/jacoco.xml" 2>/dev/null || echo "unknown")
            print_info "XML报告大小: $xml_size bytes"
            
            # 检查XML内容
            if grep -q "covered=" "$temp_reports/jacoco.xml"; then
                print_success "XML报告包含覆盖率数据"
                
                # 提取覆盖率信息
                local line_covered=$(grep -o 'type="LINE"[^>]*covered="[0-9]*"' "$temp_reports/jacoco.xml" | grep -o 'covered="[0-9]*"' | cut -d'"' -f2)
                local line_missed=$(grep -o 'type="LINE"[^>]*missed="[0-9]*"' "$temp_reports/jacoco.xml" | grep -o 'missed="[0-9]*"' | cut -d'"' -f2)
                
                if [[ -n "$line_covered" && -n "$line_missed" ]]; then
                    local total=$((line_covered + line_missed))
                    if [[ $total -gt 0 ]]; then
                        local percentage=$(echo "scale=2; $line_covered * 100 / $total" | bc 2>/dev/null || echo "计算失败")
                        print_success "检测到覆盖率: $percentage% (覆盖行数: $line_covered/$total)"
                    else
                        print_warning "总行数为0，可能项目没有代码"
                    fi
                else
                    print_warning "无法提取覆盖率数据"
                fi
            else
                print_warning "XML报告不包含覆盖率数据"
            fi
        else
            print_warning "未生成 JaCoCo XML 报告"
        fi
        
        if [[ -f "$temp_reports/scan.log" ]]; then
            print_info "生成了扫描日志"
            echo "📄 扫描日志摘要:"
            tail -10 "$temp_reports/scan.log"
        fi
        
    else
        print_error "Docker 扫描测试失败"
        
        # 显示容器日志
        print_info "检查Docker日志..."
        docker logs $(docker ps -lq) 2>/dev/null || true
    fi
    
    # 清理临时目录
    rm -rf "$temp_reports"
}

# 显示使用说明
show_usage() {
    echo ""
    print_success "🎉 增强版 JaCoCo Scanner 构建完成！"
    echo ""
    echo "📋 镜像信息:"
    docker images | grep jacoco-scanner
    echo ""
    echo "🚀 使用方法:"
    echo "1. 通过 API 自动使用:"
    echo "   python3 app.py"
    echo ""
    echo "2. 手动测试扫描:"
    echo "   docker run --rm -v \"\$(pwd)/reports:/app/reports\" jacoco-scanner:latest \\"
    echo "     --repo-url http://172.16.1.30/kian/jacocotest.git \\"
    echo "     --commit-id main \\"
    echo "     --branch main \\"
    echo "     --service-name jacocotest"
    echo ""
    echo "3. 运行诊断:"
    echo "   python3 diagnose.py"
    echo ""
    print_info "增强功能:"
    echo "   ✅ 详细的扫描日志"
    echo "   ✅ 智能的pom.xml增强"
    echo "   ✅ 覆盖率数据解析"
    echo "   ✅ 项目结构分析"
    echo "   ✅ 错误诊断和建议"
}

# 主函数
main() {
    echo "🔧 增强版 JaCoCo Scanner 构建工具"
    echo "=================================="
    
    check_docker
    check_files
    cleanup_old_images
    build_image
    test_image
    show_usage
    
    print_success "所有操作完成！"
}

# 运行主函数
main "$@"
