#!/usr/bin/env python3
"""
诊断Docker扫描卡住问题
"""

import subprocess
import time
import os

def check_docker_status():
    """检查Docker状态"""
    print("🐳 检查Docker状态")
    print("=" * 50)
    
    try:
        # 检查Docker是否运行
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Docker版本: {result.stdout.strip()}")
        else:
            print("❌ Docker未安装或未运行")
            return False
    except Exception as e:
        print(f"❌ Docker检查失败: {e}")
        return False
    
    try:
        # 检查Docker守护进程
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Docker守护进程正常运行")
        else:
            print("❌ Docker守护进程异常")
            return False
    except Exception as e:
        print(f"❌ Docker守护进程检查失败: {e}")
        return False
    
    return True

def check_docker_image():
    """检查Docker镜像"""
    print("\n🖼️ 检查Docker镜像")
    print("=" * 50)
    
    try:
        # 检查jacoco-scanner镜像
        result = subprocess.run(['docker', 'images', 'jacoco-scanner:latest'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and 'jacoco-scanner' in result.stdout:
            print("✅ jacoco-scanner:latest 镜像存在")
            print(f"镜像信息:\n{result.stdout}")
        else:
            print("❌ jacoco-scanner:latest 镜像不存在")
            print("💡 需要构建Docker镜像")
            return False
    except Exception as e:
        print(f"❌ 镜像检查失败: {e}")
        return False
    
    return True

def check_running_containers():
    """检查运行中的容器"""
    print("\n📦 检查运行中的容器")
    print("=" * 50)
    
    try:
        # 检查所有运行中的容器
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("运行中的容器:")
            print(result.stdout)
            
            # 检查是否有jacoco-scanner容器
            if 'jacoco-scanner' in result.stdout:
                print("⚠️ 发现运行中的jacoco-scanner容器")
                return True
            else:
                print("✅ 没有运行中的jacoco-scanner容器")
                return False
        else:
            print("❌ 无法获取容器列表")
            return False
    except Exception as e:
        print(f"❌ 容器检查失败: {e}")
        return False

def kill_stuck_containers():
    """终止卡住的容器"""
    print("\n🔪 终止卡住的容器")
    print("=" * 50)
    
    try:
        # 查找jacoco-scanner容器
        result = subprocess.run(['docker', 'ps', '-q', '--filter', 'ancestor=jacoco-scanner:latest'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            container_ids = result.stdout.strip().split('\n')
            print(f"找到 {len(container_ids)} 个jacoco-scanner容器")
            
            for container_id in container_ids:
                print(f"终止容器: {container_id}")
                kill_result = subprocess.run(['docker', 'kill', container_id], 
                                           capture_output=True, text=True, timeout=10)
                if kill_result.returncode == 0:
                    print(f"✅ 容器 {container_id} 已终止")
                else:
                    print(f"❌ 终止容器 {container_id} 失败")
            
            return True
        else:
            print("✅ 没有找到需要终止的容器")
            return False
            
    except Exception as e:
        print(f"❌ 终止容器失败: {e}")
        return False

def test_simple_docker_run():
    """测试简单的Docker运行"""
    print("\n🧪 测试简单Docker运行")
    print("=" * 50)
    
    try:
        # 测试简单的hello-world
        print("测试 hello-world 容器...")
        result = subprocess.run(['docker', 'run', '--rm', 'hello-world'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Docker基本功能正常")
            return True
        else:
            print("❌ Docker基本功能异常")
            print(f"错误: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Docker运行超时")
        return False
    except Exception as e:
        print(f"❌ Docker测试失败: {e}")
        return False

def check_network_connectivity():
    """检查网络连接"""
    print("\n🌐 检查网络连接")
    print("=" * 50)
    
    # 检查Git仓库连接
    try:
        print("测试Git仓库连接...")
        result = subprocess.run(['git', 'ls-remote', 'http://172.16.1.30/kian/jacocotest.git'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Git仓库连接正常")
        else:
            print("❌ Git仓库连接失败")
            print(f"错误: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Git连接超时")
        return False
    except Exception as e:
        print(f"❌ Git连接测试失败: {e}")
        return False
    
    return True

def suggest_solutions():
    """建议解决方案"""
    print("\n💡 解决方案建议")
    print("=" * 50)
    
    print("1. 如果Docker镜像不存在:")
    print("   cd /path/to/docker/build/directory")
    print("   docker build -t jacoco-scanner:latest .")
    
    print("\n2. 如果容器卡住:")
    print("   docker ps  # 查看运行中的容器")
    print("   docker kill <container_id>  # 终止卡住的容器")
    
    print("\n3. 如果网络问题:")
    print("   检查防火墙设置")
    print("   检查Git仓库访问权限")
    print("   检查Maven仓库连接")
    
    print("\n4. 临时解决方案 - 使用本地扫描:")
    print("   修改配置强制使用本地扫描而不是Docker")

def main():
    """主函数"""
    print("🔍 Docker扫描问题诊断")
    print("=" * 50)
    
    # 1. 检查Docker状态
    docker_ok = check_docker_status()
    
    # 2. 检查Docker镜像
    image_ok = check_docker_image() if docker_ok else False
    
    # 3. 检查运行中的容器
    has_running = check_running_containers() if docker_ok else False
    
    # 4. 如果有运行中的容器，尝试终止
    if has_running:
        kill_stuck_containers()
    
    # 5. 测试Docker基本功能
    docker_works = test_simple_docker_run() if docker_ok else False
    
    # 6. 检查网络连接
    network_ok = check_network_connectivity()
    
    # 总结
    print("\n📊 诊断结果")
    print("=" * 50)
    print(f"Docker状态: {'✅' if docker_ok else '❌'}")
    print(f"Docker镜像: {'✅' if image_ok else '❌'}")
    print(f"Docker功能: {'✅' if docker_works else '❌'}")
    print(f"网络连接: {'✅' if network_ok else '❌'}")
    
    if docker_ok and image_ok and docker_works and network_ok:
        print("\n🎉 Docker环境正常，可以重新尝试扫描")
    else:
        print("\n⚠️ 发现问题，建议使用本地扫描")
        suggest_solutions()
        
        # 提供快速修复命令
        print("\n🔧 快速修复命令:")
        print("# 强制使用本地扫描（临时解决方案）")
        print("# 在app.py中修改配置: use_docker = False")

if __name__ == "__main__":
    main()
