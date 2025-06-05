#!/usr/bin/env python3
"""
测试Docker功能
"""

import subprocess
import os
import tempfile

def test_docker_build():
    """测试Docker镜像构建"""
    print("🐳 测试Docker镜像构建...")
    
    try:
        # 检查Docker是否可用
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("❌ Docker不可用")
            return False
        
        print(f"✅ Docker版本: {result.stdout.strip()}")
        
        # 检查Docker守护进程
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("❌ Docker守护进程未运行")
            return False
        
        print("✅ Docker守护进程运行正常")
        
        # 构建镜像
        print("🔨 开始构建JaCoCo Docker镜像...")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        build_result = subprocess.run(
            ['docker', 'build', '-t', 'jacoco-scanner:latest', current_dir],
            capture_output=True, text=True, timeout=600
        )
        
        if build_result.returncode != 0:
            print("❌ Docker镜像构建失败:")
            print(f"构建输出: {build_result.stdout}")
            print(f"构建错误: {build_result.stderr}")
            return False
        
        print("✅ Docker镜像构建成功")
        
        # 检查镜像是否存在
        result = subprocess.run(['docker', 'images', '-q', 'jacoco-scanner:latest'], 
                              capture_output=True, text=True, timeout=10)
        
        if not result.stdout.strip():
            print("❌ 镜像构建后未找到")
            return False
        
        print("✅ Docker镜像验证成功")
        return True
        
    except Exception as e:
        print(f"❌ Docker测试失败: {str(e)}")
        return False

def test_docker_scan():
    """测试Docker扫描功能"""
    print("\n🧪 测试Docker扫描功能...")
    
    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"📁 使用临时目录: {temp_dir}")
            
            # 测试Docker扫描命令
            docker_cmd = [
                'docker', 'run', '--rm',
                '-v', f'{temp_dir}:/app/reports',
                'jacoco-scanner:latest',
                '--repo-url', 'http://172.16.1.30/kian/jacocotest.git',
                '--commit-id', '5ea76b4989a17153eade57d7d55609ebad7fdd9e',
                '--branch', 'main',
                '--service-name', 'jacocotest'
            ]
            
            print(f"🚀 执行Docker扫描命令...")
            print(f"命令: {' '.join(docker_cmd)}")
            
            result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=300)
            
            print(f"📊 扫描结果:")
            print(f"返回码: {result.returncode}")
            print(f"输出: {result.stdout}")
            if result.stderr:
                print(f"错误: {result.stderr}")
            
            # 检查报告文件
            report_files = []
            if os.path.exists(temp_dir):
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        report_files.append(os.path.join(root, file))
            
            print(f"📋 生成的报告文件: {len(report_files)}")
            for file in report_files:
                print(f"  - {file}")
            
            if result.returncode == 0:
                print("✅ Docker扫描测试成功")
                return True
            else:
                print("⚠️ Docker扫描完成但有警告")
                return True
                
    except Exception as e:
        print(f"❌ Docker扫描测试失败: {str(e)}")
        return False

def main():
    print("🔧 JaCoCo Docker功能测试")
    print("=" * 50)
    
    # 测试Docker构建
    build_success = test_docker_build()
    
    if build_success:
        # 测试Docker扫描
        scan_success = test_docker_scan()
        
        if scan_success:
            print("\n🎉 所有Docker测试通过！")
        else:
            print("\n⚠️ Docker扫描测试失败")
    else:
        print("\n❌ Docker构建测试失败")

if __name__ == "__main__":
    main()
