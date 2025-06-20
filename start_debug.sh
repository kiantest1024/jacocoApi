#!/bin/bash
# JaCoCo API 调试版本启动脚本

set -e

echo "🔍 JaCoCo API 调试版本启动脚本"
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

# 检查Python环境
check_python() {
    print_info "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        if ! command -v python &> /dev/null; then
            print_error "Python未安装"
            exit 1
        else
            PYTHON_CMD="python"
        fi
    else
        PYTHON_CMD="python3"
    fi
    
    print_success "Python命令: $PYTHON_CMD"
    
    # 检查Python版本
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    print_info "Python版本: $PYTHON_VERSION"
}

# 检查依赖
check_dependencies() {
    print_info "检查Python依赖..."
    
    if [[ -f "requirements.txt" ]]; then
        print_info "安装依赖包..."
        $PYTHON_CMD -m pip install -r requirements.txt
        print_success "依赖安装完成"
    else
        print_warning "未找到requirements.txt文件"
    fi
}

# 检查端口
check_port() {
    print_info "检查端口8003是否可用..."
    
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":8003 "; then
            print_warning "端口8003已被占用"
            print_info "尝试终止占用进程..."
            
            if command -v lsof &> /dev/null; then
                PID=$(lsof -ti:8003)
                if [[ -n "$PID" ]]; then
                    kill -9 $PID 2>/dev/null || true
                    print_info "已终止进程 $PID"
                fi
            fi
        fi
    fi
    
    print_success "端口8003可用"
}

# 清理旧日志
cleanup_logs() {
    print_info "清理旧的调试日志..."
    
    if [[ -f "jacoco_debug.log" ]]; then
        # 备份旧日志
        mv jacoco_debug.log "jacoco_debug_$(date +%Y%m%d_%H%M%S).log.bak"
        print_info "旧日志已备份"
    fi
    
    print_success "日志清理完成"
}

# 设置环境变量
setup_environment() {
    print_info "设置调试环境变量..."
    
    export CONFIG_STORAGE_TYPE=file
    export JACOCO_DEBUG_MODE=true
    export JACOCO_VERBOSE_LOGGING=true
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    print_success "环境变量设置完成"
    print_info "CONFIG_STORAGE_TYPE: $CONFIG_STORAGE_TYPE"
    print_info "JACOCO_DEBUG_MODE: $JACOCO_DEBUG_MODE"
    print_info "JACOCO_VERBOSE_LOGGING: $JACOCO_VERBOSE_LOGGING"
}

# 显示调试信息
show_debug_info() {
    print_info "调试版本信息:"
    echo "  🔍 调试模式: 启用"
    echo "  📝 详细日志: 启用"
    echo "  🌐 服务端口: 8003"
    echo "  📄 日志文件: jacoco_debug.log"
    echo "  🔗 服务地址: http://localhost:8003"
    echo "  📖 API文档: http://localhost:8003/docs"
    echo "  🔍 调试日志: http://localhost:8003/debug/logs"
    echo ""
}

# 启动服务
start_service() {
    print_info "启动JaCoCo API调试服务..."
    
    # 检查调试应用文件
    if [[ ! -f "app_debug.py" ]]; then
        print_error "调试应用文件app_debug.py不存在"
        exit 1
    fi
    
    print_success "开始启动调试服务..."
    print_warning "按 Ctrl+C 停止服务"
    echo ""
    
    # 启动应用
    $PYTHON_CMD app_debug.py
}

# 主函数
main() {
    print_info "开始启动JaCoCo API调试版本..."
    
    # 检查当前目录
    if [[ ! -f "app_debug.py" ]] && [[ ! -f "config/config.py" ]]; then
        print_error "请在jacocoApi项目根目录下运行此脚本"
        exit 1
    fi
    
    # 执行检查和启动流程
    check_python
    check_dependencies
    check_port
    cleanup_logs
    setup_environment
    show_debug_info
    start_service
}

# 信号处理
trap 'echo -e "\n${YELLOW}🔚 调试服务已停止${NC}"; exit 0' INT TERM

# 运行主函数
main "$@"
