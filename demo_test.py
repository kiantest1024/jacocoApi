"""
GitHub Webhook JaCoCo API 演示测试脚本。
用于演示和测试完整的 GitHub webhook 到 JaCoCo 覆盖率统计流程。
"""

import json
import time
import requests
import subprocess
import sys
from pathlib import Path


def check_service_health(base_url="http://localhost:8000"):
    """检查服务健康状态。"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✓ API 服务正常运行")
            return True
        else:
            print(f"✗ API 服务异常: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"✗ 无法连接到 API 服务: {str(e)}")
        return False


def test_github_webhook_ping(base_url="http://localhost:8000"):
    """测试 GitHub webhook ping 事件。"""
    print("\n=== 测试 GitHub Webhook Ping ===")
    
    webhook_url = f"{base_url}/github/webhook"
    
    # 创建 ping 负载
    ping_payload = {
        "zen": "Responsive is better than fast.",
        "hook_id": 123456789,
        "repository": {
            "name": "java-login-system",
            "full_name": "test/java-login-system",
            "clone_url": "https://github.com/test/java-login-system.git"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "ping",
        "X-GitHub-Delivery": "test-ping-123"
    }
    
    try:
        response = requests.post(webhook_url, json=ping_payload, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            print("✓ Ping 测试成功")
            return True
        else:
            print("✗ Ping 测试失败")
            return False
    except Exception as e:
        print(f"✗ Ping 测试异常: {str(e)}")
        return False


def test_github_webhook_push(base_url="http://localhost:8000"):
    """测试 GitHub webhook push 事件。"""
    print("\n=== 测试 GitHub Webhook Push ===")
    
    webhook_url = f"{base_url}/github/webhook"
    
    # 创建 push 负载
    push_payload = {
        "ref": "refs/heads/main",
        "after": "1234567890abcdef1234567890abcdef12345678",
        "repository": {
            "name": "java-login-system",
            "full_name": "your-username/java-login-system",
            "clone_url": "https://github.com/your-username/java-login-system.git"
        },
        "commits": [
            {
                "id": "1234567890abcdef1234567890abcdef12345678",
                "message": "Test commit for JaCoCo coverage",
                "author": {
                    "name": "Test User",
                    "email": "test@example.com"
                }
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": "test-push-456"
    }
    
    try:
        response = requests.post(webhook_url, json=push_payload, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "accepted":
                print("✓ Push 事件接受成功")
                task_id = result.get("task_id")
                if task_id:
                    print(f"任务 ID: {task_id}")
                    return task_id
            elif result.get("status") == "ignored":
                print("ℹ Push 事件被忽略 (可能没有配置对应的仓库)")
                return None
        else:
            print("✗ Push 测试失败")
            return None
    except Exception as e:
        print(f"✗ Push 测试异常: {str(e)}")
        return None


def check_task_status(task_id, base_url="http://localhost:8000"):
    """检查任务状态。"""
    if not task_id:
        return
    
    print(f"\n=== 检查任务状态: {task_id} ===")
    
    status_url = f"{base_url}/task/{task_id}"
    
    for i in range(5):  # 检查5次
        try:
            response = requests.get(status_url, timeout=5)
            if response.status_code == 200:
                result = response.json()
                status = result.get("status", "unknown")
                print(f"第 {i+1} 次检查 - 状态: {status}")
                
                if status == "completed":
                    print("✓ 任务完成")
                    if "result" in result:
                        scan_result = result["result"]
                        print(f"覆盖率: {scan_result.get('coverage_percentage', 0):.2f}%")
                        print(f"覆盖行数: {scan_result.get('lines_covered', 0)}")
                        print(f"总行数: {scan_result.get('lines_total', 0)}")
                    break
                elif status == "failed":
                    print("✗ 任务失败")
                    if "error" in result:
                        print(f"错误: {result['error']}")
                    break
                elif status in ["pending", "started"]:
                    print("任务进行中...")
                    time.sleep(10)  # 等待10秒再检查
                else:
                    print(f"未知状态: {status}")
                    break
            else:
                print(f"✗ 无法获取任务状态: {response.status_code}")
                break
        except Exception as e:
            print(f"✗ 检查任务状态异常: {str(e)}")
            break


def test_local_jacoco_scan():
    """测试本地 JaCoCo 扫描。"""
    print("\n=== 测试本地 JaCoCo 扫描 ===")
    
    # 检查是否在 java-login-system 目录
    java_project_path = Path("../java-login-system")
    if not java_project_path.exists():
        print("✗ 未找到 java-login-system 项目")
        return False
    
    pom_file = java_project_path / "pom.xml"
    if not pom_file.exists():
        print("✗ 未找到 pom.xml 文件")
        return False
    
    print("✓ 找到 Java 项目")
    
    try:
        # 运行 Maven 测试和 JaCoCo 报告
        print("运行 Maven 测试和 JaCoCo 报告...")
        result = subprocess.run([
            "mvn", "clean", "test", "jacoco:report"
        ], cwd=java_project_path, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✓ Maven 测试和 JaCoCo 报告生成成功")
            
            # 检查报告文件
            jacoco_xml = java_project_path / "target" / "site" / "jacoco" / "jacoco.xml"
            jacoco_html = java_project_path / "target" / "site" / "jacoco" / "index.html"
            
            if jacoco_xml.exists():
                print(f"✓ JaCoCo XML 报告: {jacoco_xml}")
            else:
                print("✗ 未找到 JaCoCo XML 报告")
            
            if jacoco_html.exists():
                print(f"✓ JaCoCo HTML 报告: {jacoco_html}")
            else:
                print("✗ 未找到 JaCoCo HTML 报告")
            
            return True
        else:
            print("✗ Maven 执行失败")
            print(f"错误输出: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        print("✗ Maven 执行超时")
        return False
    except Exception as e:
        print(f"✗ Maven 执行异常: {str(e)}")
        return False


def main():
    """主函数。"""
    print("========================================")
    print("GitHub Webhook JaCoCo API 演示测试")
    print("========================================")
    
    # 检查服务健康状态
    if not check_service_health():
        print("\n请先启动 API 服务:")
        print("  python start_github_webhook.py")
        print("  或")
        print("  python quick_start.py")
        return
    
    # 测试 GitHub webhook
    test_github_webhook_ping()
    task_id = test_github_webhook_push()
    
    # 如果有任务ID，检查任务状态
    if task_id:
        check_task_status(task_id)
    
    # 测试本地 JaCoCo 扫描
    test_local_jacoco_scan()
    
    print("\n========================================")
    print("演示测试完成")
    print("========================================")
    print("\n下一步:")
    print("1. 配置您的 GitHub 仓库 webhook")
    print("2. 在 config.py 中添加您的仓库配置")
    print("3. 推送代码到 GitHub 触发自动扫描")


if __name__ == "__main__":
    main()
