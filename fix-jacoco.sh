#!/bin/bash

# JaCoCo 覆盖率问题快速修复脚本
set -e

echo "🔧 JaCoCo 覆盖率问题快速修复工具"
echo "=================================="

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Docker状态
check_docker() {
    echo "🐳 检查 Docker 状态..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker 未安装"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "❌ Docker 服务未运行"
        echo "💡 请启动 Docker Desktop 后重试"
        return 1
    fi
    
    echo "✅ Docker 服务正常"
    return 0
}

# 构建JaCoCo扫描器镜像
build_scanner() {
    echo "🔨 构建 JaCoCo 扫描器镜像..."
    
    if docker images | grep -q "jacoco-scanner.*latest"; then
        echo "📋 发现现有镜像，是否重新构建？(y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "⏭️  跳过镜像构建"
            return 0
        fi
    fi
    
    echo "🔨 开始构建镜像..."
    if docker build -f docker/Dockerfile.alpine -t jacoco-scanner:latest docker/; then
        echo "✅ 镜像构建成功"
        return 0
    else
        echo "❌ 镜像构建失败"
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
        echo "✅ 仓库克隆成功"
        
        # 检查项目结构
        if [[ -f "$temp_dir/test/pom.xml" ]]; then
            echo "✅ 找到 Maven 项目"
            
            # 检查测试代码
            if find "$temp_dir/test/src/test" -name "*.java" 2>/dev/null | grep -q .; then
                echo "✅ 找到测试代码"
            else
                echo "⚠️  未找到测试代码，这可能是覆盖率为0的原因"
                echo "💡 建议检查项目是否包含单元测试"
            fi
        else
            echo "❌ 不是 Maven 项目"
        fi
    else
        echo "❌ 仓库克隆失败"
        echo "💡 请检查网络连接和仓库地址"
    fi
    
    # 清理临时目录
    rm -rf "$temp_dir"
}

# 检查本地Maven环境
check_maven() {
    echo "📦 检查 Maven 环境..."
    
    if command -v mvn &> /dev/null; then
        echo "✅ Maven 已安装: $(mvn --version | head -1)"
        return 0
    else
        echo "❌ Maven 未安装"
        echo "💡 请安装 Maven 以支持本地扫描"
        return 1
    fi
}

# 运行诊断
run_diagnosis() {
    echo "🔍 运行完整诊断..."
    
    if [[ -f "diagnose.py" ]]; then
        python3 diagnose.py
    else
        echo "❌ 诊断脚本不存在"
    fi
}

# 主菜单
show_menu() {
    echo ""
    echo "请选择操作："
    echo "1) 检查 Docker 环境"
    echo "2) 构建 JaCoCo 扫描器镜像"
    echo "3) 测试扫描功能"
    echo "4) 检查 Maven 环境"
    echo "5) 运行完整诊断"
    echo "6) 一键修复（推荐）"
    echo "0) 退出"
    echo ""
    echo -n "请输入选择 [0-6]: "
}

# 一键修复
auto_fix() {
    echo "🚀 开始一键修复..."
    
    local success=true
    
    # 1. 检查Docker
    if check_docker; then
        echo "✅ Docker 检查通过"
    else
        echo "❌ Docker 检查失败"
        success=false
    fi
    
    # 2. 构建镜像（如果Docker可用）
    if [[ "$success" == "true" ]]; then
        if build_scanner; then
            echo "✅ 镜像构建成功"
        else
            echo "❌ 镜像构建失败"
            success=false
        fi
    fi
    
    # 3. 检查Maven
    if check_maven; then
        echo "✅ Maven 检查通过"
    else
        echo "⚠️  Maven 检查失败（本地扫描可能不可用）"
    fi
    
    # 4. 测试扫描
    test_scan
    
    # 5. 运行诊断
    run_diagnosis
    
    echo ""
    if [[ "$success" == "true" ]]; then
        echo "🎉 修复完成！JaCoCo 扫描应该可以正常工作了。"
        echo ""
        echo "💡 如果仍然遇到覆盖率为0的问题，请检查："
        echo "   1. 目标项目是否包含单元测试"
        echo "   2. 测试是否能够正常运行"
        echo "   3. JaCoCo 插件配置是否正确"
    else
        echo "⚠️  修复过程中遇到问题，请手动解决上述错误。"
    fi
}

# 主循环
main() {
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1) check_docker ;;
            2) build_scanner ;;
            3) test_scan ;;
            4) check_maven ;;
            5) run_diagnosis ;;
            6) auto_fix ;;
            0) echo "👋 再见！"; exit 0 ;;
            *) echo "❌ 无效选择，请重试" ;;
        esac
        
        echo ""
        echo "按 Enter 继续..."
        read -r
    done
}

# 如果直接运行脚本，显示菜单
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi
