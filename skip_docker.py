#!/usr/bin/env python3
"""
跳过Docker，直接使用本地扫描
"""

import os
import sys

def disable_docker_scan():
    """禁用Docker扫描，强制使用本地扫描"""
    
    # 修改jacoco_tasks.py，让Docker扫描总是失败
    jacoco_tasks_path = "jacoco_tasks.py"
    
    if not os.path.exists(jacoco_tasks_path):
        print("❌ 找不到jacoco_tasks.py文件")
        return False
    
    # 读取文件
    with open(jacoco_tasks_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换Docker扫描函数，让它总是抛出异常
    old_docker_scan = 'def _run_docker_scan('
    new_docker_scan = '''def _run_docker_scan(
    repo_url: str,
    commit_id: str,
    branch_name: str,
    reports_dir: str,
    service_config: Dict[str, Any],
    request_id: str
) -> Dict[str, Any]:
    """
    Docker扫描已禁用，直接抛出异常以使用本地扫描
    """
    raise Exception("Docker扫描已禁用，使用本地扫描")

def _run_docker_scan_disabled('''
    
    if old_docker_scan in content:
        # 找到函数结束位置
        start_pos = content.find(old_docker_scan)
        if start_pos != -1:
            # 找到下一个函数定义
            next_func_pos = content.find('\ndef ', start_pos + 1)
            if next_func_pos == -1:
                next_func_pos = len(content)
            
            # 替换整个函数
            before = content[:start_pos]
            after = content[next_func_pos:]
            
            new_content = before + new_docker_scan + after
            
            # 写回文件
            with open(jacoco_tasks_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ 已禁用Docker扫描，将强制使用本地扫描")
            return True
    
    print("⚠️ 未找到Docker扫描函数，可能已经修改过")
    return False

def check_local_dependencies():
    """检查本地扫描依赖"""
    import subprocess
    
    dependencies = [
        ("git", "git --version"),
        ("maven", "mvn --version"),
        ("java", "java -version")
    ]
    
    print("🔍 检查本地扫描依赖:")
    all_ok = True
    
    for name, cmd in dependencies:
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  ✅ {name}: 可用")
            else:
                print(f"  ❌ {name}: 不可用")
                all_ok = False
        except Exception as e:
            print(f"  ❌ {name}: 检查失败 - {e}")
            all_ok = False
    
    return all_ok

def main():
    print("======================================")
    print("跳过Docker，配置本地扫描")
    print("======================================")
    
    # 检查依赖
    if not check_local_dependencies():
        print("\n❌ 本地依赖不完整，请先安装:")
        print("Ubuntu: sudo apt install git maven openjdk-11-jdk")
        print("Windows: 安装Git、Maven、Java")
        return
    
    # 禁用Docker扫描
    if disable_docker_scan():
        print("\n🎉 配置完成！")
        print("现在所有扫描都将使用本地Maven执行")
        print("\n🚀 重启服务以应用更改:")
        print("python3 app.py")
    else:
        print("\n❌ 配置失败")

if __name__ == "__main__":
    main()
