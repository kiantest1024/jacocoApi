#!/usr/bin/env python3
"""
JaCoCo API 诊断脚本
用于检查和诊断 JaCoCo 扫描问题
"""

import os
import subprocess
import sys
import json
import tempfile
from pathlib import Path

def check_docker():
    """检查Docker环境"""
    print("🐳 检查 Docker 环境...")
    
    try:
        # 检查Docker命令
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Docker 已安装: {result.stdout.strip()}")
        else:
            print("❌ Docker 命令执行失败")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Docker 未安装或不可用")
        return False
    
    try:
        # 检查Docker服务
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Docker 服务正在运行")
        else:
            print("❌ Docker 服务未运行")
            print("💡 请启动 Docker Desktop")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Docker 服务响应超时")
        return False
    
    # 检查JaCoCo扫描器镜像
    try:
        result = subprocess.run(['docker', 'images', '-q', 'jacoco-scanner:latest'], 
                              capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            print("✅ jacoco-scanner:latest 镜像存在")
            return True
        else:
            print("❌ jacoco-scanner:latest 镜像不存在")
            print("💡 请运行: bash build-scanner.sh")
            return False
    except subprocess.TimeoutExpired:
        print("❌ 检查Docker镜像超时")
        return False

def check_maven():
    """检查Maven环境"""
    print("\n📦 检查 Maven 环境...")

    try:
        result = subprocess.run(['mvn', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ Maven 已安装: {version_line}")

            # 检查 JAVA_HOME
            java_home_line = [line for line in result.stdout.split('\n') if 'Java home' in line]
            if java_home_line:
                print(f"✅ Java 环境: {java_home_line[0].strip()}")

            return True
        else:
            print("❌ Maven 命令执行失败")
            print(f"错误输出: {result.stderr}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Maven 未安装或不可用")
        print("💡 Linux 安装命令:")
        print("   Ubuntu/Debian: sudo apt install maven")
        print("   CentOS/RHEL: sudo yum install maven")
        print("   或下载: https://maven.apache.org/install.html")
        return False

def check_git():
    """检查Git环境"""
    print("\n🔧 检查 Git 环境...")
    
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Git 已安装: {result.stdout.strip()}")
            return True
        else:
            print("❌ Git 命令执行失败")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Git 未安装或不可用")
        return False

def test_local_scan():
    """测试本地扫描功能"""
    print("\n🧪 测试本地扫描功能...")
    
    # 测试仓库URL
    test_repo = "http://172.16.1.30/kian/jacocotest.git"
    
    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = os.path.join(temp_dir, "test_repo")
            
            print(f"📥 克隆测试仓库: {test_repo}")
            result = subprocess.run(['git', 'clone', test_repo, repo_dir], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                print(f"❌ 克隆仓库失败: {result.stderr}")
                return False
            
            print("✅ 仓库克隆成功")
            
            # 检查是否为Maven项目
            pom_path = os.path.join(repo_dir, "pom.xml")
            if os.path.exists(pom_path):
                print("✅ 找到 pom.xml 文件")
                
                # 检查源代码结构
                src_main = os.path.join(repo_dir, "src", "main", "java")
                src_test = os.path.join(repo_dir, "src", "test", "java")
                
                has_main = os.path.exists(src_main) and any(
                    f.endswith('.java') for _, _, files in os.walk(src_main) for f in files
                )
                has_test = os.path.exists(src_test) and any(
                    f.endswith('.java') for _, _, files in os.walk(src_test) for f in files
                )
                
                print(f"📁 主代码: {'✅' if has_main else '❌'}")
                print(f"📁 测试代码: {'✅' if has_test else '❌'}")
                
                if not has_test:
                    print("⚠️  没有测试代码，覆盖率将为 0%")
                
                return True
            else:
                print("❌ 不是 Maven 项目，未找到 pom.xml")
                return False
                
    except Exception as e:
        print(f"❌ 测试本地扫描失败: {e}")
        return False

def check_config():
    """检查配置"""
    print("\n⚙️  检查配置...")

    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, "config", "config.py")

    if os.path.exists(config_file):
        print("✅ 配置文件存在")

        # 检查jacocotest项目配置
        try:
            import sys
            sys.path.insert(0, script_dir)
            from config.config import get_service_config

            test_repo = "http://172.16.1.30/kian/jacocotest.git"
            config = get_service_config(test_repo)

            print(f"📋 项目配置:")
            print(f"   服务名: {config.get('service_name')}")
            print(f"   机器人ID: {config.get('bot_id')}")
            print(f"   机器人名: {config.get('bot_name')}")
            print(f"   通知启用: {config.get('enable_notifications')}")

            return True
        except Exception as e:
            print(f"❌ 读取配置失败: {e}")
            return False
    else:
        print(f"❌ 配置文件不存在: {config_file}")
        return False

def main():
    """主函数"""
    print("🔍 JaCoCo API 诊断工具")
    print("=" * 50)
    
    results = []
    
    # 检查各个组件
    results.append(("Docker", check_docker()))
    results.append(("Maven", check_maven()))
    results.append(("Git", check_git()))
    results.append(("配置", check_config()))
    results.append(("本地扫描", test_local_scan()))
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 诊断结果:")
    
    all_passed = True
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有检查通过！JaCoCo API 应该可以正常工作。")
    else:
        print("⚠️  发现问题，请根据上述提示进行修复。")
        print("\n💡 常见解决方案:")
        print("1. 启动 Docker Desktop")
        print("2. 运行: bash build-scanner.sh")
        print("3. 检查网络连接到 172.16.1.30")
        print("4. 确保测试仓库有测试代码")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
