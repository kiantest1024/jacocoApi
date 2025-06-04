#!/usr/bin/env python3
"""
调试共享容器问题
检查容器状态和扫描过程
"""

import subprocess
import json
import os
import time

def check_docker_containers():
    """检查Docker容器状态"""
    print("🐳 检查Docker容器状态")
    print("=" * 50)
    
    try:
        # 检查所有运行中的容器
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, timeout=10)
        print("运行中的容器:")
        print(result.stdout)
        
        # 检查jacoco-scanner相关容器
        result = subprocess.run(['docker', 'ps', '--filter', 'name=jacoco'], 
                              capture_output=True, text=True, timeout=10)
        if result.stdout.strip():
            print("\nJaCoCo相关容器:")
            print(result.stdout)
        else:
            print("\n❌ 未找到JaCoCo相关容器")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 检查容器失败: {e}")
        return False

def check_shared_work_directory():
    """检查共享工作目录"""
    print("\n📁 检查共享工作目录")
    print("=" * 50)
    
    work_dir = "/tmp/jacoco_shared_work"
    
    if os.path.exists(work_dir):
        print(f"✅ 共享工作目录存在: {work_dir}")
        
        # 列出目录内容
        try:
            items = os.listdir(work_dir)
            if items:
                print("目录内容:")
                for item in items:
                    item_path = os.path.join(work_dir, item)
                    if os.path.isdir(item_path):
                        print(f"  📁 {item}/")
                        # 列出子目录内容
                        try:
                            sub_items = os.listdir(item_path)
                            for sub_item in sub_items[:5]:  # 只显示前5个
                                print(f"    📄 {sub_item}")
                            if len(sub_items) > 5:
                                print(f"    ... 还有 {len(sub_items) - 5} 个文件")
                        except:
                            pass
                    else:
                        print(f"  📄 {item}")
            else:
                print("目录为空")
        except Exception as e:
            print(f"❌ 读取目录失败: {e}")
        
        return True
    else:
        print(f"❌ 共享工作目录不存在: {work_dir}")
        return False

def test_container_exec():
    """测试容器执行命令"""
    print("\n🧪 测试容器执行")
    print("=" * 50)
    
    try:
        # 获取容器ID
        result = subprocess.run(['docker', 'ps', '-q', '--filter', 'name=jacoco-scanner-shared'], 
                              capture_output=True, text=True, timeout=10)
        
        if not result.stdout.strip():
            print("❌ 未找到共享容器")
            return False
        
        container_id = result.stdout.strip()
        print(f"找到容器ID: {container_id}")
        
        # 测试基本命令
        print("\n测试基本命令...")
        test_commands = [
            ['ls', '-la', '/app'],
            ['ls', '-la', '/app/shared_work'],
            ['which', 'mvn'],
            ['which', 'git'],
            ['which', 'jq']
        ]
        
        for cmd in test_commands:
            try:
                result = subprocess.run(['docker', 'exec', container_id] + cmd,
                                      capture_output=True, text=True, timeout=10)
                print(f"  {' '.join(cmd)}: {'✅' if result.returncode == 0 else '❌'}")
                if result.returncode != 0:
                    print(f"    错误: {result.stderr.strip()}")
            except Exception as e:
                print(f"  {' '.join(cmd)}: ❌ 异常: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试容器执行失败: {e}")
        return False

def test_manual_scan():
    """手动测试扫描过程"""
    print("\n🔧 手动测试扫描")
    print("=" * 50)
    
    try:
        # 获取容器ID
        result = subprocess.run(['docker', 'ps', '-q', '--filter', 'name=jacoco-scanner-shared'], 
                              capture_output=True, text=True, timeout=10)
        
        if not result.stdout.strip():
            print("❌ 未找到共享容器")
            return False
        
        container_id = result.stdout.strip()
        
        # 创建测试任务配置
        test_config = {
            "repo_url": "http://172.16.1.30/kian/jacocotest.git",
            "commit_id": "5ea76b4989a17153eade57d7d55609ebad7fdd9e",
            "branch_name": "main",
            "service_name": "jacocotest",
            "request_id": "debug_test",
            "task_dir": "/app/shared_work/task_debug_test"
        }
        
        # 在容器中创建任务目录和配置文件
        print("创建测试任务...")
        
        # 创建任务目录
        subprocess.run(['docker', 'exec', container_id, 'mkdir', '-p', '/app/shared_work/task_debug_test'],
                      capture_output=True, timeout=10)
        
        # 写入配置文件
        config_json = json.dumps(test_config, indent=2)
        subprocess.run(['docker', 'exec', '-i', container_id, 'tee', '/app/shared_work/task_debug_test/task_config.json'],
                      input=config_json, text=True, capture_output=True, timeout=10)
        
        # 检查扫描脚本是否存在
        result = subprocess.run(['docker', 'exec', container_id, 'ls', '-la', '/app/scripts/'],
                              capture_output=True, text=True, timeout=10)
        print("容器内脚本目录:")
        print(result.stdout)
        
        # 检查shared_scan.sh是否存在
        result = subprocess.run(['docker', 'exec', container_id, 'ls', '-la', '/app/scripts/shared_scan.sh'],
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ 找到shared_scan.sh脚本")
            
            # 执行扫描脚本
            print("\n执行扫描脚本...")
            result = subprocess.run(['docker', 'exec', container_id, 
                                   '/app/scripts/shared_scan.sh', 
                                   '/app/shared_work/task_debug_test/task_config.json'],
                                  capture_output=True, text=True, timeout=300)
            
            print(f"扫描返回码: {result.returncode}")
            print("扫描输出:")
            print(result.stdout)
            
            if result.stderr:
                print("扫描错误:")
                print(result.stderr)
            
            # 检查结果文件
            result = subprocess.run(['docker', 'exec', container_id, 'ls', '-la', '/app/shared_work/task_debug_test/'],
                                  capture_output=True, text=True, timeout=10)
            print("\n任务目录内容:")
            print(result.stdout)
            
            # 检查结果文件内容
            result = subprocess.run(['docker', 'exec', container_id, 'cat', '/app/shared_work/task_debug_test/scan_result.json'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("\n扫描结果:")
                print(result.stdout)
            else:
                print("❌ 未找到扫描结果文件")
            
        else:
            print("❌ 未找到shared_scan.sh脚本")
            print("容器内可能缺少扫描脚本")
            
            # 检查是否有其他扫描脚本
            result = subprocess.run(['docker', 'exec', container_id, 'find', '/app', '-name', '*.sh'],
                                  capture_output=True, text=True, timeout=10)
            print("容器内的shell脚本:")
            print(result.stdout)
        
        return True
        
    except Exception as e:
        print(f"❌ 手动测试失败: {e}")
        return False

def check_docker_image():
    """检查Docker镜像"""
    print("\n🖼️ 检查Docker镜像")
    print("=" * 50)
    
    try:
        # 检查jacoco-scanner镜像
        result = subprocess.run(['docker', 'images', 'jacoco-scanner'], 
                              capture_output=True, text=True, timeout=10)
        print("JaCoCo Scanner镜像:")
        print(result.stdout)
        
        # 检查镜像内容
        result = subprocess.run(['docker', 'run', '--rm', 'jacoco-scanner:latest', 'ls', '-la', '/app'],
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("\n镜像内/app目录内容:")
            print(result.stdout)
        else:
            print("❌ 无法检查镜像内容")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查镜像失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 共享Docker容器调试")
    print("=" * 50)
    
    # 1. 检查Docker容器
    containers_ok = check_docker_containers()
    
    # 2. 检查共享工作目录
    work_dir_ok = check_shared_work_directory()
    
    # 3. 检查Docker镜像
    image_ok = check_docker_image()
    
    # 4. 测试容器执行
    exec_ok = test_container_exec() if containers_ok else False
    
    # 5. 手动测试扫描
    scan_ok = test_manual_scan() if containers_ok else False
    
    # 总结
    print("\n" + "=" * 50)
    print("📋 调试结果总结:")
    print(f"  Docker容器: {'✅ 正常' if containers_ok else '❌ 异常'}")
    print(f"  工作目录: {'✅ 正常' if work_dir_ok else '❌ 异常'}")
    print(f"  Docker镜像: {'✅ 正常' if image_ok else '❌ 异常'}")
    print(f"  容器执行: {'✅ 正常' if exec_ok else '❌ 异常'}")
    print(f"  扫描测试: {'✅ 正常' if scan_ok else '❌ 异常'}")
    
    if not containers_ok:
        print("\n💡 建议:")
        print("  1. 检查Docker服务是否运行")
        print("  2. 启动共享容器: curl -X POST http://localhost:8002/docker/start")
    
    if not image_ok:
        print("\n💡 建议:")
        print("  1. 检查jacoco-scanner镜像是否存在")
        print("  2. 重新构建Docker镜像")
    
    if containers_ok and not scan_ok:
        print("\n💡 建议:")
        print("  1. 检查容器内是否有shared_scan.sh脚本")
        print("  2. 检查脚本权限和依赖")
        print("  3. 查看详细的扫描日志")

if __name__ == "__main__":
    main()
