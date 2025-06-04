#!/usr/bin/env python3
"""
确认本地扫描模式配置
"""

import os
import json

def check_config():
    """检查配置文件"""
    print("🔍 检查配置文件...")
    
    config_file = "config.py"
    if not os.path.exists(config_file):
        print("❌ 配置文件不存在")
        return False
    
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键配置
    checks = [
        ('use_docker": False', "Docker已禁用"),
        ('force_local_scan": True', "强制本地扫描已启用"),
        ('scan_method": "local"', "扫描方法设为本地")
    ]
    
    all_good = True
    for check, desc in checks:
        if check in content:
            print(f"  ✅ {desc}")
        else:
            print(f"  ❌ {desc} - 未找到")
            all_good = False
    
    return all_good

def check_dependencies():
    """检查本地依赖"""
    import subprocess
    
    print("\n🔍 检查本地依赖...")
    
    dependencies = [
        ("Git", "git", "--version"),
        ("Maven", "mvn", "--version"),
        ("Java", "java", "-version")
    ]
    
    all_good = True
    for name, cmd, arg in dependencies:
        try:
            result = subprocess.run([cmd, arg], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = (result.stdout or result.stderr).split('\n')[0]
                print(f"  ✅ {name}: {version_line}")
            else:
                print(f"  ❌ {name}: 命令执行失败")
                all_good = False
        except FileNotFoundError:
            print(f"  ❌ {name}: 未安装")
            all_good = False
        except Exception as e:
            print(f"  ❌ {name}: 检查失败 - {e}")
            all_good = False
    
    return all_good

def show_status():
    """显示当前状态"""
    print("\n" + "="*50)
    print("JaCoCo扫描服务状态")
    print("="*50)
    
    config_ok = check_config()
    deps_ok = check_dependencies()
    
    print(f"\n📊 总体状态:")
    if config_ok and deps_ok:
        print("  ✅ 系统已配置为本地扫描模式")
        print("  ✅ 所有依赖都已安装")
        print("  🚀 可以正常使用JaCoCo扫描功能")
        
        print(f"\n🎯 使用方法:")
        print("  1. 启动服务: python3 app.py")
        print("  2. 测试扫描: python3 test_local_only.py")
        print("  3. 发送webhook到: http://localhost:8002/github/webhook-no-auth")
        
        print(f"\n💡 优势:")
        print("  • 无需Docker，启动更快")
        print("  • 直接使用本地Maven，更稳定")
        print("  • 完整功能：扫描、报告、通知")
        
    else:
        print("  ⚠️ 配置或依赖有问题")
        
        if not config_ok:
            print("  🔧 配置问题：请检查config.py文件")
        
        if not deps_ok:
            print("  🔧 依赖问题：请安装缺失的工具")
            print("     Ubuntu: sudo apt install git maven openjdk-11-jdk")
            print("     Windows: 手动安装Git、Maven、Java")
    
    print(f"\n📋 关于Docker:")
    print("  • Docker构建遇到网络问题")
    print("  • 本地扫描功能完全等效")
    print("  • 可以稍后解决Docker问题")
    print("  • 当前配置优先使用本地扫描")

if __name__ == "__main__":
    show_status()
