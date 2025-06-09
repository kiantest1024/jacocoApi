#!/bin/bash

# Linux环境配置脚本
# 用于解决数据不一致和通知问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 设置环境变量
setup_environment() {
    log_info "设置环境变量..."
    
    # 创建环境变量文件
    cat > .env << EOF
# JaCoCo API 配置
CONFIG_STORAGE_TYPE=mysql
MYSQL_HOST=172.16.1.30
MYSQL_PORT=3306
MYSQL_DATABASE=jacoco_config
MYSQL_USER=jacoco
MYSQL_PASSWORD=asd301325..

# Java环境
JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
PATH=\$PATH:\$JAVA_HOME/bin

# Maven配置
MAVEN_OPTS="-Xmx1024m"
EOF
    
    # 导出环境变量
    export CONFIG_STORAGE_TYPE=mysql
    export MYSQL_HOST=172.16.1.30
    export MYSQL_PORT=3306
    export MYSQL_DATABASE=jacoco_config
    export MYSQL_USER=jacoco
    export MYSQL_PASSWORD=asd301325..
    
    log_success "环境变量设置完成"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p reports
    mkdir -p logs
    mkdir -p temp
    
    # 设置权限
    chmod 755 reports logs temp
    
    log_success "目录创建完成"
}

# 测试MySQL连接
test_mysql() {
    log_info "测试MySQL连接..."
    
    if command -v mysql &> /dev/null; then
        if mysql -h 172.16.1.30 -u jacoco -pasd301325.. -e "SELECT 1;" jacoco_config &> /dev/null; then
            log_success "MySQL连接正常"
            return 0
        else
            log_error "MySQL连接失败"
            return 1
        fi
    else
        log_warning "MySQL客户端未安装"
        return 1
    fi
}

# 启动服务
start_service() {
    log_info "启动JaCoCo API服务..."
    
    # 设置环境变量
    source .env 2>/dev/null || true
    export $(cat .env | grep -v '^#' | xargs) 2>/dev/null || true
    
    # 检查是否已有服务在运行
    if pgrep -f "python.*app.py" > /dev/null; then
        log_warning "服务已在运行，正在重启..."
        pkill -f "python.*app.py" || true
        sleep 3
    fi
    
    # 启动服务
    nohup python3 app.py > logs/jacoco-api.log 2>&1 &
    echo $! > jacoco-api.pid
    
    # 等待服务启动
    sleep 5
    
    # 检查服务状态
    if curl -f http://localhost:8002/health > /dev/null 2>&1; then
        log_success "服务启动成功"
        log_info "访问地址: http://localhost:8002/config"
        log_info "日志文件: logs/jacoco-api.log"
        return 0
    else
        log_error "服务启动失败"
        return 1
    fi
}

# 同步配置数据
sync_config() {
    log_info "同步配置数据..."
    
    # 等待服务完全启动
    sleep 3
    
    # 添加项目配置
    python3 -c "
import requests
import json

projects = [
    {
        'project_name': 'jacocotest',
        'git_url': 'http://172.16.1.30/kian/jacocotest.git',
        'bot_id': 'default'
    },
    {
        'project_name': 'backend-lotto-game',
        'git_url': 'http://172.16.1.30/kian/backend-lotto-game.git', 
        'bot_id': 'default'
    }
]

for project in projects:
    try:
        response = requests.post(
            'http://localhost:8002/config/mapping',
            json=project,
            timeout=10
        )
        if response.status_code == 200:
            print(f'✅ 添加项目: {project[\"project_name\"]}')
        else:
            print(f'⚠️  项目 {project[\"project_name\"]}: {response.status_code}')
    except Exception as e:
        print(f'❌ 添加项目 {project[\"project_name\"]} 失败: {e}')
"
    
    log_success "配置同步完成"
}

# 测试功能
test_functionality() {
    log_info "测试功能..."
    
    # 运行排查脚本
    if [ -f "linux_debug.py" ]; then
        python3 linux_debug.py
    else
        log_warning "排查脚本不存在，跳过详细测试"
    fi
}

# 显示状态
show_status() {
    echo ""
    echo "=" * 60
    log_info "服务状态"
    echo "=" * 60
    
    # 检查进程
    if pgrep -f "python.*app.py" > /dev/null; then
        PID=$(pgrep -f "python.*app.py")
        log_success "服务运行中 (PID: $PID)"
    else
        log_error "服务未运行"
    fi
    
    # 检查端口
    if netstat -tlnp 2>/dev/null | grep :8002 > /dev/null; then
        log_success "端口8002已监听"
    else
        log_error "端口8002未监听"
    fi
    
    # 检查健康状态
    if curl -f http://localhost:8002/health > /dev/null 2>&1; then
        log_success "健康检查通过"
    else
        log_error "健康检查失败"
    fi
    
    echo ""
    log_info "访问地址:"
    echo "   Web界面: http://localhost:8002/config"
    echo "   API文档: http://localhost:8002/docs"
    echo "   健康检查: http://localhost:8002/health"
    
    echo ""
    log_info "日志文件:"
    echo "   应用日志: logs/jacoco-api.log"
    echo "   进程ID: jacoco-api.pid"
    
    echo ""
    log_info "管理命令:"
    echo "   查看日志: tail -f logs/jacoco-api.log"
    echo "   停止服务: kill \$(cat jacoco-api.pid)"
    echo "   重启服务: $0"
}

# 主函数
main() {
    echo "🔧 Linux环境配置脚本"
    echo "=" * 60
    
    # 1. 设置环境变量
    setup_environment
    
    # 2. 创建目录
    create_directories
    
    # 3. 测试MySQL连接
    test_mysql
    
    # 4. 启动服务
    if start_service; then
        # 5. 同步配置
        sync_config
        
        # 6. 测试功能
        test_functionality
        
        # 7. 显示状态
        show_status
    else
        log_error "服务启动失败，请检查日志"
        if [ -f "logs/jacoco-api.log" ]; then
            echo ""
            log_info "最近的日志:"
            tail -20 logs/jacoco-api.log
        fi
    fi
}

# 执行主函数
main "$@"
