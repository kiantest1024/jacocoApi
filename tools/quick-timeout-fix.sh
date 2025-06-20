#!/bin/bash
# 快速修复 Docker 扫描超时问题

set -e

echo "🔧 Docker 扫描超时问题快速修复"
echo "================================"

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

# 检查正在运行的 JaCoCo 容器
check_running_containers() {
    print_info "检查正在运行的 JaCoCo 容器..."
    
    CONTAINERS=$(docker ps --filter "ancestor=jacoco-scanner:latest" --format "{{.ID}} {{.Status}}" 2>/dev/null || echo "")
    
    if [[ -n "$CONTAINERS" ]]; then
        print_warning "发现正在运行的 JaCoCo 容器:"
        echo "$CONTAINERS"
        
        read -p "是否强制停止这些容器? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "停止容器..."
            docker ps --filter "ancestor=jacoco-scanner:latest" --format "{{.ID}}" | xargs -r docker kill
            print_success "容器已停止"
        fi
    else
        print_success "没有正在运行的 JaCoCo 容器"
    fi
}

# 测试 Docker 镜像
test_docker_image() {
    print_info "测试 Docker 镜像..."
    
    if ! docker images -q jacoco-scanner:latest | grep -q .; then
        print_error "JaCoCo Docker 镜像不存在"
        print_info "请运行: ./tools/build.sh 构建镜像"
        return 1
    fi
    
    print_success "Docker 镜像存在"
    
    # 快速测试镜像
    print_info "快速测试镜像启动..."
    
    if timeout 30 docker run --rm jacoco-scanner:latest --help >/dev/null 2>&1; then
        print_success "Docker 镜像可以正常启动"
    else
        print_warning "Docker 镜像启动测试超时或失败"
    fi
}

# 测试网络连接
test_network() {
    print_info "测试网络连接..."
    
    REPO_URL="http://172.16.1.30/kian/jacocotest.git"
    
    if timeout 10 curl -s --head "$REPO_URL" >/dev/null 2>&1; then
        print_success "Git 仓库网络连接正常"
    else
        print_warning "Git 仓库网络连接可能有问题"
        print_info "测试 URL: $REPO_URL"
    fi
}

# 运行快速扫描测试
run_quick_test() {
    print_info "运行快速扫描测试 (60秒超时)..."
    
    # 创建临时目录
    TEMP_DIR=$(mktemp -d)
    print_info "临时目录: $TEMP_DIR"
    
    # 构建测试命令
    TEST_CMD="docker run --rm -v $TEMP_DIR:/workspace/reports jacoco-scanner:latest --repo-url http://172.16.1.30/kian/jacocotest.git --commit-id main --branch main --service-name jacocotest"
    
    print_info "测试命令: $TEST_CMD"
    
    # 运行测试
    if timeout 60 $TEST_CMD; then
        print_success "快速测试完成"
        
        # 检查结果
        if [[ -f "$TEMP_DIR/jacoco.xml" ]]; then
            print_success "生成了 JaCoCo 报告"
        else
            print_warning "未生成 JaCoCo 报告"
        fi
        
        # 显示生成的文件
        print_info "生成的文件:"
        ls -la "$TEMP_DIR" || echo "目录为空"
        
    else
        print_error "快速测试失败或超时"
        
        # 检查是否有部分结果
        if [[ -d "$TEMP_DIR" ]]; then
            print_info "检查部分结果:"
            ls -la "$TEMP_DIR" || echo "目录为空"
        fi
    fi
    
    # 清理
    rm -rf "$TEMP_DIR"
}

# 检查系统资源
check_system_resources() {
    print_info "检查系统资源..."
    
    # 检查磁盘空间
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $DISK_USAGE -gt 90 ]]; then
        print_warning "磁盘使用率过高: ${DISK_USAGE}%"
    else
        print_success "磁盘空间充足: ${DISK_USAGE}% 已使用"
    fi
    
    # 检查内存
    if command -v free >/dev/null 2>&1; then
        MEM_INFO=$(free -h | grep "Mem:")
        print_info "内存使用情况: $MEM_INFO"
    fi
    
    # 检查 Docker 状态
    if docker system df >/dev/null 2>&1; then
        print_info "Docker 存储使用情况:"
        docker system df
    fi
}

# 生成优化建议
generate_recommendations() {
    print_info "生成优化建议..."
    
    cat << 'EOF'

🎯 优化建议:

1. 🕐 调整超时时间:
   - 调试模式使用较短超时 (5分钟)
   - 正常模式使用较长超时 (30分钟)

2. 🔍 使用监控工具:
   python tools/docker-scan-monitor.py

3. 📊 检查项目复杂度:
   - 大型项目可能需要更长时间
   - 考虑拆分测试或使用本地扫描

4. 🚀 性能优化:
   - 确保 Docker 有足够资源
   - 检查网络连接稳定性
   - 清理 Docker 缓存: docker system prune

5. 🔧 故障排除:
   - 查看容器日志: docker logs <container_id>
   - 使用本地扫描作为备选方案
   - 检查项目的 Maven 配置

EOF
}

# 主函数
main() {
    print_info "开始诊断 Docker 扫描超时问题..."
    
    # 检查 Docker 是否可用
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker 未安装"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker 服务未运行"
        exit 1
    fi
    
    # 执行检查步骤
    check_running_containers
    echo
    
    test_docker_image
    echo
    
    test_network
    echo
    
    check_system_resources
    echo
    
    # 询问是否运行快速测试
    read -p "是否运行快速扫描测试? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo
        run_quick_test
        echo
    fi
    
    generate_recommendations
    
    print_success "诊断完成！"
}

# 运行主函数
main "$@"
