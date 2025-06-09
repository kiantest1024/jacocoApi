#!/bin/bash

# JaCoCo API Ubuntu 快速部署脚本
# 使用方法: ./deploy-ubuntu.sh [direct|docker|service]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统
check_system() {
    log_info "检查系统环境..."
    
    # 检查Ubuntu版本
    if ! grep -q "Ubuntu" /etc/os-release; then
        log_error "此脚本仅支持Ubuntu系统"
        exit 1
    fi
    
    # 检查权限
    if [[ $EUID -eq 0 ]]; then
        log_warning "建议不要使用root用户运行此脚本"
    fi
    
    log_success "系统检查通过"
}

# 安装系统依赖
install_dependencies() {
    log_info "安装系统依赖..."
    
    sudo apt update
    sudo apt install -y \
        python3 \
        python3-pip \
        git \
        maven \
        openjdk-11-jdk \
        curl \
        mysql-client
    
    log_success "系统依赖安装完成"
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        log_success "Python依赖安装完成"
    else
        log_error "未找到requirements.txt文件"
        exit 1
    fi
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."
    
    cat > .env << EOF
CONFIG_STORAGE_TYPE=mysql
MYSQL_HOST=172.16.1.30
MYSQL_PORT=3306
MYSQL_DATABASE=jacoco_config
MYSQL_USER=jacoco
MYSQL_PASSWORD=asd301325..
EOF
    
    log_success "环境变量配置完成"
}

# 测试MySQL连接
test_mysql_connection() {
    log_info "测试MySQL连接..."
    
    if mysql -h 172.16.1.30 -u jacoco -pasd301325.. -e "SELECT 1;" > /dev/null 2>&1; then
        log_success "MySQL连接测试成功"
    else
        log_warning "MySQL连接测试失败，请检查数据库配置"
    fi
}

# 直接部署
deploy_direct() {
    log_info "开始直接部署..."
    
    check_system
    install_dependencies
    install_python_deps
    setup_environment
    test_mysql_connection
    
    log_info "启动JaCoCo API服务..."
    source .env
    export $(cat .env | xargs)
    
    # 后台启动
    nohup python3 start.py > jacoco-api.log 2>&1 &
    echo $! > jacoco-api.pid
    
    sleep 5
    
    # 检查服务状态
    if curl -f http://localhost:8002/health > /dev/null 2>&1; then
        log_success "JaCoCo API服务启动成功！"
        log_info "访问地址: http://localhost:8002/config"
        log_info "日志文件: jacoco-api.log"
        log_info "进程ID文件: jacoco-api.pid"
    else
        log_error "服务启动失败，请检查日志"
        exit 1
    fi
}

# Docker部署
deploy_docker() {
    log_info "开始Docker部署..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker build -f Dockerfile.api -t jacoco-api:ubuntu .
    
    # 停止现有容器
    if docker ps -q -f name=jacoco-api; then
        log_info "停止现有容器..."
        docker stop jacoco-api
        docker rm jacoco-api
    fi
    
    # 启动新容器
    log_info "启动Docker容器..."
    docker run -d \
        --name jacoco-api \
        -p 8002:8002 \
        -e CONFIG_STORAGE_TYPE=mysql \
        -e MYSQL_HOST=172.16.1.30 \
        -e MYSQL_USER=jacoco \
        -e MYSQL_PASSWORD=asd301325.. \
        -v $(pwd)/reports:/app/reports \
        jacoco-api:ubuntu
    
    sleep 10
    
    # 检查容器状态
    if docker ps -q -f name=jacoco-api; then
        log_success "Docker容器启动成功！"
        log_info "访问地址: http://localhost:8002/config"
        log_info "查看日志: docker logs -f jacoco-api"
    else
        log_error "Docker容器启动失败"
        docker logs jacoco-api
        exit 1
    fi
}

# 系统服务部署
deploy_service() {
    log_info "开始系统服务部署..."
    
    check_system
    install_dependencies
    install_python_deps
    setup_environment
    test_mysql_connection
    
    # 创建systemd服务文件
    log_info "创建systemd服务..."
    
    sudo tee /etc/systemd/system/jacoco-api.service > /dev/null << EOF
[Unit]
Description=JaCoCo API Service
After=network.target mysql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=CONFIG_STORAGE_TYPE=mysql
Environment=MYSQL_HOST=172.16.1.30
Environment=MYSQL_USER=jacoco
Environment=MYSQL_PASSWORD=asd301325..
ExecStart=/usr/bin/python3 start.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # 启用并启动服务
    sudo systemctl daemon-reload
    sudo systemctl enable jacoco-api
    sudo systemctl start jacoco-api
    
    sleep 5
    
    # 检查服务状态
    if sudo systemctl is-active --quiet jacoco-api; then
        log_success "系统服务启动成功！"
        log_info "访问地址: http://localhost:8002/config"
        log_info "服务状态: sudo systemctl status jacoco-api"
        log_info "查看日志: sudo journalctl -u jacoco-api -f"
    else
        log_error "系统服务启动失败"
        sudo systemctl status jacoco-api
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "JaCoCo API Ubuntu 部署脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 direct   - 直接运行部署"
    echo "  $0 docker   - Docker容器部署"
    echo "  $0 service  - 系统服务部署"
    echo ""
    echo "示例:"
    echo "  $0 direct   # 推荐用于开发环境"
    echo "  $0 service  # 推荐用于生产环境"
    echo "  $0 docker   # 推荐用于容器化环境"
}

# 主函数
main() {
    case "${1:-}" in
        "direct")
            deploy_direct
            ;;
        "docker")
            deploy_docker
            ;;
        "service")
            deploy_service
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "无效的部署方式: ${1:-}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
