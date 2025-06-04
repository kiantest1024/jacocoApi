#!/usr/bin/env python3
"""
JaCoCo扫描问题诊断脚本
用于诊断和修复常见的扫描问题
"""

import subprocess
import os
import requests
import json

def check_docker_environment():
    """检查Docker环境"""
    print("🐳 检查Docker环境")
    
    try:
        # 检查Docker是否可用
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker版本: {result.stdout.strip()}")
        else:
            print("❌ Docker不可用")
            return False
        
        # 检查镜像是否存在
        result = subprocess.run(["docker", "images", "jacoco-scanner:latest"], capture_output=True, text=True)
        if "jacoco-scanner" in result.stdout:
            print("✅ JaCoCo Scanner镜像存在")
        else:
            print("❌ JaCoCo Scanner镜像不存在")
            print("💡 请运行: ./rebuild-docker.sh")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Docker检查失败: {e}")
        return False

def check_maven_environment():
    """检查Maven环境"""
    print("\n📦 检查Maven环境")
    
    try:
        result = subprocess.run(["mvn", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Maven版本: {result.stdout.split('\\n')[0]}")
            return True
        else:
            print("❌ Maven不可用")
            return False
    except Exception as e:
        print(f"❌ Maven检查失败: {e}")
        return False

def test_docker_scan():
    """测试Docker扫描功能"""
    print("\n🧪 测试Docker扫描功能")
    
    # 创建测试目录
    test_dir = "/tmp/jacoco_test_reports"
    os.makedirs(test_dir, exist_ok=True)
    
    # 测试Docker命令
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{test_dir}:/app/reports",
        "-v", f"{os.getcwd()}/repos:/app/repos",
        "jacoco-scanner:latest",
        "/app/scripts/scan.sh",
        "--repo-url", "https://gitlab.complexdevops.com/kian/jacocoTest.git",
        "--commit-id", "main",
        "--branch", "main",
        "--service-name", "jacocoTest"
    ]
    
    print("🚀 执行Docker扫描测试...")
    print(f"命令: {' '.join(docker_cmd)}")
    
    try:
        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=300)
        
        print(f"返回码: {result.returncode}")
        print(f"输出: {result.stdout}")
        if result.stderr:
            print(f"错误: {result.stderr}")
        
        if result.returncode == 0:
            print("✅ Docker扫描测试成功")
            return True
        else:
            print("❌ Docker扫描测试失败")
            
            # 分析错误
            if "MaxPermSize" in result.stderr:
                print("🔧 检测到MaxPermSize问题，请重新构建Docker镜像")
            elif "Non-resolvable parent POM" in result.stdout:
                print("🔧 检测到父POM解析问题，这是正常的，系统会自动回退")
            
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Docker扫描测试超时")
        return False
    except Exception as e:
        print(f"❌ Docker扫描测试异常: {e}")
        return False

def test_webhook_scan():
    """测试Webhook扫描"""
    print("\n🔗 测试Webhook扫描")
    
    # 检查服务是否运行
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code != 200:
            print("❌ JaCoCo API服务未运行")
            print("💡 请先启动服务: python app.py")
            return False
    except Exception as e:
        print("❌ 无法连接到JaCoCo API服务")
        print("💡 请先启动服务: python app.py")
        return False
    
    # 发送测试webhook
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": "backend-base-api-auto-build",
            "http_url": "http://172.16.1.30/kian/backend-base-api-auto-build.git"
        },
        "user_name": "test_user",
        "commits": [
            {
                "id": "test_diagnosis",
                "message": "Test diagnosis scan"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    try:
        print("📤 发送测试webhook...")
        response = requests.post(
            "http://localhost:8002/github/webhook-no-auth",
            json=webhook_data,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook处理成功")
            
            # 检查扫描结果
            scan_result = result.get('scan_result', {})
            status = scan_result.get('status', 'unknown')
            print(f"扫描状态: {status}")
            
            if 'maven_output' in scan_result:
                maven_output = scan_result['maven_output']
                if "Non-resolvable parent POM" in maven_output:
                    print("⚠️ 检测到父POM解析问题（这是预期的）")
                    print("💡 系统应该会自动尝试回退方案")
            
            return True
        else:
            print(f"❌ Webhook处理失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook测试异常: {e}")
        return False

def provide_solutions():
    """提供解决方案"""
    print("\n💡 常见问题解决方案")
    print("=" * 50)
    
    print("\n1. MaxPermSize错误:")
    print("   - 问题: Java 8+不支持MaxPermSize参数")
    print("   - 解决: 重新构建Docker镜像")
    print("   - 命令: ./rebuild-docker.sh")
    
    print("\n2. 父POM解析失败:")
    print("   - 问题: 项目依赖私有仓库中的父POM")
    print("   - 解决: 系统会自动尝试回退方案")
    print("   - 状态: 这是正常现象，不影响扫描")
    
    print("\n3. Docker镜像不存在:")
    print("   - 问题: 未构建JaCoCo Scanner镜像")
    print("   - 解决: 构建Docker镜像")
    print("   - 命令: ./build-docker.sh")
    
    print("\n4. 服务连接失败:")
    print("   - 问题: JaCoCo API服务未启动")
    print("   - 解决: 启动服务")
    print("   - 命令: python app.py")
    
    print("\n5. 网络连接问题:")
    print("   - 问题: 无法访问Git仓库或Maven仓库")
    print("   - 解决: 检查网络连接和防火墙设置")

def main():
    """主函数"""
    print("🔍 JaCoCo扫描问题诊断")
    print("=" * 50)
    
    # 检查环境
    docker_ok = check_docker_environment()
    maven_ok = check_maven_environment()
    
    if not docker_ok:
        print("\n❌ Docker环境有问题，请先修复")
        provide_solutions()
        return
    
    if not maven_ok:
        print("\n⚠️ Maven环境有问题，但Docker扫描可能仍然可用")
    
    # 测试功能
    print("\n" + "=" * 50)
    user_input = input("🤔 是否要测试Docker扫描功能？(y/N): ").strip().lower()
    if user_input in ['y', 'yes']:
        test_docker_scan()
    
    print("\n" + "=" * 50)
    user_input = input("🤔 是否要测试Webhook扫描功能？(y/N): ").strip().lower()
    if user_input in ['y', 'yes']:
        test_webhook_scan()
    
    # 提供解决方案
    provide_solutions()
    
    print("\n🎉 诊断完成！")

if __name__ == "__main__":
    main()
