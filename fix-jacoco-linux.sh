#!/bin/bash

# JaCoCo 覆盖率问题 Linux 环境修复脚本
set -e

echo "🔧 JaCoCo 覆盖率问题 Linux 环境修复工具"
echo "========================================"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色消息
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}💡 $1${NC}"; }

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "检测到root用户，某些操作可能需要调整权限"
        return 0
    fi
    return 1
}

# 检查Docker状态
check_docker() {
    echo "🐳 检查 Docker 环境..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        print_info "安装命令:"
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install docker.io"
        echo "  CentOS/RHEL: sudo yum install docker"
        echo "  或参考: https://docs.docker.com/engine/install/"
        return 1
    fi
    
    print_success "Docker 已安装: $(docker --version)"
    
    if ! docker info &> /dev/null; then
        print_error "Docker 服务未运行"
        print_info "启动 Docker 服务:"
        echo "  sudo systemctl start docker"
        echo "  sudo systemctl enable docker"
        
        # 尝试启动Docker服务
        echo "是否尝试启动 Docker 服务？(y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            if sudo systemctl start docker; then
                print_success "Docker 服务启动成功"
                sleep 2
            else
                print_error "Docker 服务启动失败"
                return 1
            fi
        else
            return 1
        fi
    fi
    
    print_success "Docker 服务正在运行"
    
    # 检查用户是否在docker组中
    if ! groups | grep -q docker; then
        print_warning "当前用户不在 docker 组中"
        print_info "添加用户到 docker 组:"
        echo "  sudo usermod -aG docker \$USER"
        echo "  然后重新登录或运行: newgrp docker"
    fi
    
    return 0
}

# 检查Maven环境
check_maven() {
    echo "📦 检查 Maven 环境..."
    
    if ! command -v mvn &> /dev/null; then
        print_error "Maven 未安装"
        print_info "安装命令:"
        echo "  Ubuntu/Debian: sudo apt install maven"
        echo "  CentOS/RHEL: sudo yum install maven"
        return 1
    fi
    
    print_success "Maven 已安装"
    mvn --version | head -3
    
    # 检查JAVA_HOME
    if [[ -z "$JAVA_HOME" ]]; then
        print_warning "JAVA_HOME 未设置"
        print_info "设置 JAVA_HOME:"
        echo "  export JAVA_HOME=/usr/lib/jvm/default-java"
        echo "  或添加到 ~/.bashrc"
    else
        print_success "JAVA_HOME: $JAVA_HOME"
    fi
    
    return 0
}

# 构建JaCoCo扫描器镜像
build_scanner() {
    echo "🔨 构建 JaCoCo 扫描器镜像..."
    
    if docker images | grep -q "jacoco-scanner.*latest"; then
        echo "📋 发现现有镜像，是否重新构建？(y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "跳过镜像构建"
            return 0
        fi
    fi
    
    echo "🔨 开始构建镜像..."
    if docker build -f docker/Dockerfile.alpine -t jacoco-scanner:latest docker/; then
        print_success "镜像构建成功"
        echo "📋 镜像信息:"
        docker images | grep jacoco-scanner
        return 0
    else
        print_error "镜像构建失败"
        return 1
    fi
}

# 测试扫描功能
test_scan() {
    echo "🧪 测试扫描功能..."
    
    local test_repo="http://172.16.1.30/kian/jacocotest.git"
    local temp_dir=$(mktemp -d)
    
    echo "📥 测试仓库克隆..."
    if git clone "$test_repo" "$temp_dir/test" &> /dev/null; then
        print_success "仓库克隆成功"
        
        # 检查项目结构
        if [[ -f "$temp_dir/test/pom.xml" ]]; then
            print_success "找到 Maven 项目"
            
            # 检查测试代码
            if find "$temp_dir/test/src/test" -name "*.java" 2>/dev/null | grep -q .; then
                print_success "找到测试代码"
                
                # 尝试运行测试
                echo "是否尝试运行项目测试？(y/N)"
                read -r response
                if [[ "$response" =~ ^[Yy]$ ]]; then
                    cd "$temp_dir/test"
                    if mvn clean test -q; then
                        print_success "测试运行成功"
                    else
                        print_warning "测试运行失败，但这不影响覆盖率扫描"
                    fi
                    cd "$SCRIPT_DIR"
                fi
            else
                print_warning "未找到测试代码，这可能是覆盖率为0的原因"
                print_info "建议检查项目是否包含单元测试"
            fi
        else
            print_error "不是 Maven 项目"
        fi
    else
        print_error "仓库克隆失败"
        print_info "请检查网络连接和仓库地址"
    fi
    
    # 清理临时目录
    rm -rf "$temp_dir"
}

# 运行诊断
run_diagnosis() {
    echo "🔍 运行完整诊断..."
    
    if [[ -f "diagnose.py" ]]; then
        python3 diagnose.py
    else
        print_error "诊断脚本不存在"
    fi
}

# 测试Docker扫描
test_docker_scan() {
    echo "🧪 测试 Docker 扫描..."
    
    if ! docker images | grep -q "jacoco-scanner.*latest"; then
        print_error "jacoco-scanner 镜像不存在，请先构建镜像"
        return 1
    fi
    
    local temp_reports=$(mktemp -d)
    
    echo "📊 运行 Docker 扫描测试..."
    if docker run --rm \
        -v "$temp_reports:/app/reports" \
        jacoco-scanner:latest \
        --repo-url http://172.16.1.30/kian/jacocotest.git \
        --commit-id main \
        --branch main \
        --service-name jacocotest; then
        
        print_success "Docker 扫描测试成功"
        
        # 检查生成的报告
        if [[ -f "$temp_reports/jacoco.xml" ]]; then
            print_success "生成了 JaCoCo XML 报告"
            
            # 简单解析覆盖率
            if command -v xmllint &> /dev/null; then
                local line_coverage=$(xmllint --xpath "//counter[@type='LINE']/@covered" "$temp_reports/jacoco.xml" 2>/dev/null | sed 's/covered="//g' | sed 's/"//g')
                local line_total=$(xmllint --xpath "//counter[@type='LINE']/@missed" "$temp_reports/jacoco.xml" 2>/dev/null | sed 's/missed="//g' | sed 's/"//g')
                
                if [[ -n "$line_coverage" && -n "$line_total" ]]; then
                    local total=$((line_coverage + line_total))
                    if [[ $total -gt 0 ]]; then
                        local percentage=$(echo "scale=2; $line_coverage * 100 / $total" | bc 2>/dev/null || echo "计算失败")
                        print_success "行覆盖率: $percentage%"
                    fi
                fi
            fi
        else
            print_warning "未生成 JaCoCo XML 报告"
        fi
        
        if [[ -d "$temp_reports/html" ]]; then
            print_success "生成了 HTML 报告"
        fi
    else
        print_error "Docker 扫描测试失败"
    fi
    
    # 清理临时目录
    rm -rf "$temp_reports"
}

# 一键修复
auto_fix() {
    echo "🚀 开始一键修复..."
    
    local success=true
    
    # 1. 检查Docker
    if check_docker; then
        print_success "Docker 检查通过"
    else
        print_error "Docker 检查失败"
        success=false
    fi
    
    # 2. 检查Maven
    if check_maven; then
        print_success "Maven 检查通过"
    else
        print_warning "Maven 检查失败（但不影响 Docker 扫描）"
    fi
    
    # 3. 构建镜像（如果Docker可用）
    if [[ "$success" == "true" ]]; then
        if build_scanner; then
            print_success "镜像构建成功"
        else
            print_error "镜像构建失败"
            success=false
        fi
    fi
    
    # 4. 测试扫描
    if [[ "$success" == "true" ]]; then
        test_docker_scan
    fi
    
    # 5. 运行诊断
    run_diagnosis
    
    echo ""
    if [[ "$success" == "true" ]]; then
        print_success "修复完成！JaCoCo 扫描应该可以正常工作了。"
        echo ""
        print_info "如果仍然遇到覆盖率为0的问题，请检查："
        echo "   1. 目标项目是否包含单元测试"
        echo "   2. 测试是否能够正常运行"
        echo "   3. JaCoCo 插件配置是否正确"
    else
        print_warning "修复过程中遇到问题，请手动解决上述错误。"
    fi
}

# 主菜单
show_menu() {
    echo ""
    echo "请选择操作："
    echo "1) 检查 Docker 环境"
    echo "2) 检查 Maven 环境"
    echo "3) 构建 JaCoCo 扫描器镜像"
    echo "4) 测试 Docker 扫描"
    echo "5) 测试项目扫描功能"
    echo "6) 运行完整诊断"
    echo "7) 一键修复（推荐）"
    echo "0) 退出"
    echo ""
    echo -n "请输入选择 [0-7]: "
}

# 主循环
main() {
    # 检查是否为Linux环境
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_warning "此脚本专为 Linux 环境设计"
        print_info "Windows 用户请使用: fix-jacoco.sh 或 build-scanner.bat"
    fi
    
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1) check_docker ;;
            2) check_maven ;;
            3) build_scanner ;;
            4) test_docker_scan ;;
            5) test_scan ;;
            6) run_diagnosis ;;
            7) auto_fix ;;
            0) echo "👋 再见！"; exit 0 ;;
            *) print_error "无效选择，请重试" ;;
        esac
        
        echo ""
        echo "按 Enter 继续..."
        read -r
    done
}

# 如果直接运行脚本，显示菜单
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
