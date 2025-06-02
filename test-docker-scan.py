"""
Docker JaCoCo 扫描测试脚本。
用于测试 Docker 容器中的 JaCoCo 覆盖率扫描功能。
"""

import os
import sys
import subprocess
import tempfile
import shutil
import json
from pathlib import Path


def check_docker():
    """检查 Docker 是否可用。"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Docker 可用: {result.stdout.strip()}")
            return True
        else:
            print("✗ Docker 不可用")
            return False
    except FileNotFoundError:
        print("✗ Docker 未安装")
        return False


def check_docker_image(image_name="jacoco-scanner:latest"):
    """检查 Docker 镜像是否存在。"""
    try:
        result = subprocess.run(['docker', 'images', '-q', image_name], capture_output=True, text=True)
        if result.stdout.strip():
            print(f"✓ Docker 镜像存在: {image_name}")
            return True
        else:
            print(f"✗ Docker 镜像不存在: {image_name}")
            return False
    except Exception as e:
        print(f"✗ 检查 Docker 镜像失败: {str(e)}")
        return False


def build_docker_image():
    """构建 Docker 镜像。"""
    print("构建 Docker 镜像...")
    
    try:
        # 检查构建脚本是否存在
        build_script = "build-docker.sh"
        if os.path.exists(build_script):
            print("使用构建脚本...")
            if os.name == 'nt':  # Windows
                result = subprocess.run(['bash', build_script], capture_output=True, text=True)
            else:
                result = subprocess.run(['./build-docker.sh'], capture_output=True, text=True)
        else:
            print("直接使用 docker build...")
            result = subprocess.run([
                'docker', 'build', 
                '-t', 'jacoco-scanner:latest',
                '-f', 'docker/Dockerfile.jacoco-scanner',
                '.'
            ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Docker 镜像构建成功")
            print(result.stdout)
            return True
        else:
            print("✗ Docker 镜像构建失败")
            print(f"错误: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ 构建 Docker 镜像异常: {str(e)}")
        return False


def test_docker_scan_local():
    """测试本地 Java 项目的 Docker 扫描。"""
    print("\n=== 测试本地 Java 项目 Docker 扫描 ===")
    
    # 检查本地 Java 项目
    java_project_path = Path("../java-login-system").resolve()
    if not java_project_path.exists():
        print("✗ 未找到本地 Java 项目")
        return False
    
    print(f"✓ 找到 Java 项目: {java_project_path}")
    
    # 创建临时报告目录
    reports_dir = tempfile.mkdtemp(prefix="jacoco_test_reports_")
    print(f"报告目录: {reports_dir}")
    
    try:
        # 构建 Docker 运行命令
        docker_cmd = [
            'docker', 'run', '--rm',
            '-v', f'{reports_dir}:/app/reports',
            '-v', f'{java_project_path}:/app/workspace/project:ro',
            'jacoco-scanner:latest',
            '/app/scripts/scan.sh',
            '--project-path', '/app/workspace/project',
            '--reports-path', '/app/reports'
        ]
        
        print("执行 Docker 扫描...")
        print(f"命令: {' '.join(docker_cmd)}")
        
        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✓ Docker 扫描成功")
            print("Docker 输出:")
            print(result.stdout)
            
            # 检查生成的报告
            check_reports(reports_dir)
            return True
        else:
            print("✗ Docker 扫描失败")
            print(f"错误: {result.stderr}")
            print(f"输出: {result.stdout}")
            return False
    
    except subprocess.TimeoutExpired:
        print("✗ Docker 扫描超时")
        return False
    except Exception as e:
        print(f"✗ Docker 扫描异常: {str(e)}")
        return False
    finally:
        # 清理报告目录
        if os.path.exists(reports_dir):
            shutil.rmtree(reports_dir)
            print(f"已清理报告目录: {reports_dir}")


def test_docker_scan_git():
    """测试 Git 仓库的 Docker 扫描。"""
    print("\n=== 测试 Git 仓库 Docker 扫描 ===")
    
    # 使用测试仓库 URL
    repo_url = "https://github.com/test/java-login-system.git"
    commit_id = "main"  # 使用分支名作为提交ID进行测试
    branch_name = "main"
    
    # 创建临时报告目录
    reports_dir = tempfile.mkdtemp(prefix="jacoco_git_test_reports_")
    print(f"报告目录: {reports_dir}")
    
    try:
        # 构建 Docker 运行命令
        docker_cmd = [
            'docker', 'run', '--rm',
            '-v', f'{reports_dir}:/app/reports',
            'jacoco-scanner:latest',
            '--repo-url', repo_url,
            '--commit-id', commit_id,
            '--branch', branch_name
        ]
        
        print("执行 Docker Git 扫描...")
        print(f"命令: {' '.join(docker_cmd)}")
        
        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✓ Docker Git 扫描成功")
            print("Docker 输出:")
            print(result.stdout)
            
            # 检查生成的报告
            check_reports(reports_dir)
            return True
        else:
            print("✗ Docker Git 扫描失败")
            print(f"错误: {result.stderr}")
            print(f"输出: {result.stdout}")
            return False
    
    except subprocess.TimeoutExpired:
        print("✗ Docker Git 扫描超时")
        return False
    except Exception as e:
        print(f"✗ Docker Git 扫描异常: {str(e)}")
        return False
    finally:
        # 清理报告目录
        if os.path.exists(reports_dir):
            shutil.rmtree(reports_dir)
            print(f"已清理报告目录: {reports_dir}")


def check_reports(reports_dir):
    """检查生成的报告文件。"""
    print("\n检查生成的报告:")
    
    # 检查 XML 报告
    xml_report = os.path.join(reports_dir, "jacoco.xml")
    if os.path.exists(xml_report):
        print(f"✓ JaCoCo XML 报告: {xml_report}")
        print(f"  文件大小: {os.path.getsize(xml_report)} 字节")
    else:
        print("✗ 未找到 JaCoCo XML 报告")
    
    # 检查 HTML 报告
    html_report_dir = os.path.join(reports_dir, "html")
    if os.path.exists(html_report_dir):
        print(f"✓ JaCoCo HTML 报告: {html_report_dir}")
        html_files = list(Path(html_report_dir).glob("*.html"))
        print(f"  HTML 文件数量: {len(html_files)}")
    else:
        print("✗ 未找到 JaCoCo HTML 报告")
    
    # 检查摘要 JSON
    summary_json = os.path.join(reports_dir, "summary.json")
    if os.path.exists(summary_json):
        print(f"✓ 报告摘要: {summary_json}")
        try:
            with open(summary_json, 'r', encoding='utf-8') as f:
                summary = json.load(f)
                if "coverage" in summary and "line" in summary["coverage"]:
                    coverage = summary["coverage"]["line"]["percentage"]
                    print(f"  行覆盖率: {coverage}%")
        except Exception as e:
            print(f"  读取摘要失败: {str(e)}")
    else:
        print("✗ 未找到报告摘要")
    
    # 列出所有文件
    print("\n报告目录内容:")
    for root, dirs, files in os.walk(reports_dir):
        level = root.replace(reports_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            print(f"{subindent}{file} ({file_size} 字节)")


def main():
    """主函数。"""
    print("========================================")
    print("Docker JaCoCo 扫描测试")
    print("========================================")
    
    # 检查 Docker
    if not check_docker():
        print("请安装 Docker 后重试")
        return
    
    # 检查 Docker 镜像
    if not check_docker_image():
        print("Docker 镜像不存在，尝试构建...")
        if not build_docker_image():
            print("无法构建 Docker 镜像，退出")
            return
    
    # 测试本地项目扫描
    success_local = test_docker_scan_local()
    
    # 测试 Git 仓库扫描（可选）
    print("\n是否测试 Git 仓库扫描？(y/n): ", end="")
    if input().lower().startswith('y'):
        success_git = test_docker_scan_git()
    else:
        success_git = None
    
    # 总结
    print("\n========================================")
    print("测试结果总结:")
    print(f"本地项目扫描: {'✓ 成功' if success_local else '✗ 失败'}")
    if success_git is not None:
        print(f"Git 仓库扫描: {'✓ 成功' if success_git else '✗ 失败'}")
    print("========================================")


if __name__ == "__main__":
    main()
