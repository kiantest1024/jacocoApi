#!/usr/bin/env python3
"""
Docker问题自动修复脚本
"""

import subprocess
import os
import sys

def run_command(cmd, timeout=30):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"
    except Exception as e:
        return -1, "", str(e)

def check_docker():
    """检查Docker状态"""
    print("🔍 检查Docker状态...")
    
    # 检查Docker命令
    code, out, err = run_command("docker --version")
    if code != 0:
        print("❌ Docker命令不可用")
        return False
    
    print(f"✅ Docker版本: {out.strip()}")
    
    # 检查Docker守护进程
    code, out, err = run_command("docker info")
    if code != 0:
        print("❌ Docker守护进程未运行")
        print(f"错误: {err}")
        return False
    
    print("✅ Docker守护进程运行正常")
    return True

def check_image():
    """检查Docker镜像"""
    print("\n🔍 检查JaCoCo Docker镜像...")
    
    code, out, err = run_command("docker images -q jacoco-scanner:latest")
    if code != 0 or not out.strip():
        print("❌ JaCoCo Docker镜像不存在")
        return False
    
    print("✅ JaCoCo Docker镜像存在")
    
    # 测试镜像是否能正常启动
    print("🧪 测试镜像启动...")
    code, out, err = run_command("docker run --rm jacoco-scanner:latest --help", timeout=60)
    
    if code != 0:
        print("❌ Docker镜像启动失败")
        print(f"错误输出: {err}")
        return False
    
    print("✅ Docker镜像测试通过")
    return True

def rebuild_image():
    """重建Docker镜像"""
    print("\n🔨 重建Docker镜像...")
    
    # 删除旧镜像
    print("🗑️ 删除旧镜像...")
    run_command("docker rmi jacoco-scanner:latest", timeout=30)
    
    # 清理缓存
    print("🧹 清理Docker缓存...")
    run_command("docker system prune -f", timeout=60)
    
    # 重新构建
    print("🔨 构建新镜像...")
    code, out, err = run_command("docker build --no-cache -t jacoco-scanner:latest .", timeout=600)
    
    if code != 0:
        print("❌ Docker镜像构建失败")
        print(f"构建输出: {out}")
        print(f"构建错误: {err}")
        return False
    
    print("✅ Docker镜像构建成功")
    return True

def test_docker_scan():
    """测试Docker扫描功能"""
    print("\n🧪 测试Docker扫描功能...")
    
    # 创建临时目录
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = f"""docker run --rm -v {temp_dir}:/app/reports jacoco-scanner:latest \
--repo-url http://172.16.1.30/kian/jacocotest.git \
--commit-id 5ea76b4989a17153eade57d7d55609ebad7fdd9e \
--branch main \
--service-name jacocotest"""
        
        print(f"执行命令: {cmd}")
        code, out, err = run_command(cmd, timeout=300)
        
        print(f"返回码: {code}")
        print(f"输出: {out}")
        if err:
            print(f"错误: {err}")
        
        if code == 0:
            print("✅ Docker扫描测试成功")
            return True
        else:
            print("❌ Docker扫描测试失败")
            return False

def main():
    print("🔧 JaCoCo Docker问题自动修复")
    print("=" * 50)
    
    # 检查Docker环境
    if not check_docker():
        print("\n❌ Docker环境不可用，请先安装并启动Docker")
        sys.exit(1)
    
    # 检查镜像
    image_ok = check_image()
    
    if not image_ok:
        print("\n🔄 镜像有问题，开始重建...")
        if not rebuild_image():
            print("\n❌ 镜像重建失败")
            sys.exit(1)
        
        # 重新检查镜像
        if not check_image():
            print("\n❌ 重建后镜像仍有问题")
            sys.exit(1)
    
    # 测试扫描功能
    if test_docker_scan():
        print("\n🎉 Docker功能修复完成！")
        print("现在可以正常使用Docker扫描功能了。")
    else:
        print("\n⚠️ Docker镜像构建成功，但扫描测试失败")
        print("建议检查网络连接和仓库访问权限。")

if __name__ == "__main__":
    main()
