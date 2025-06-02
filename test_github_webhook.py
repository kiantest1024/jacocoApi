"""
GitHub Webhook 测试脚本。
用于测试 GitHub webhook 接口的功能。
"""

import json
import requests
import hashlib
import hmac
from typing import Dict, Any


def create_github_signature(payload: str, secret: str) -> str:
    """
    创建 GitHub webhook 签名。
    
    参数:
        payload: JSON 负载字符串
        secret: webhook 密钥
        
    返回:
        签名字符串
    """
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


def create_test_push_payload() -> Dict[str, Any]:
    """
    创建测试用的 GitHub push 事件负载。
    
    返回:
        测试负载字典
    """
    return {
        "ref": "refs/heads/main",
        "before": "0000000000000000000000000000000000000000",
        "after": "1234567890abcdef1234567890abcdef12345678",
        "repository": {
            "id": 123456789,
            "name": "java-login-system",
            "full_name": "your-username/java-login-system",
            "clone_url": "https://github.com/your-username/java-login-system.git",
            "ssh_url": "git@github.com:your-username/java-login-system.git"
        },
        "commits": [
            {
                "id": "1234567890abcdef1234567890abcdef12345678",
                "message": "Add JaCoCo coverage support",
                "author": {
                    "name": "Test User",
                    "email": "test@example.com"
                },
                "url": "https://github.com/your-username/java-login-system/commit/1234567890abcdef1234567890abcdef12345678"
            }
        ],
        "head_commit": {
            "id": "1234567890abcdef1234567890abcdef12345678",
            "message": "Add JaCoCo coverage support",
            "author": {
                "name": "Test User",
                "email": "test@example.com"
            }
        },
        "pusher": {
            "name": "test-user",
            "email": "test@example.com"
        }
    }


def create_test_ping_payload() -> Dict[str, Any]:
    """
    创建测试用的 GitHub ping 事件负载。
    
    返回:
        测试负载字典
    """
    return {
        "zen": "Responsive is better than fast.",
        "hook_id": 123456789,
        "hook": {
            "type": "Repository",
            "id": 123456789,
            "name": "web",
            "active": True,
            "events": ["push"],
            "config": {
                "content_type": "json",
                "insecure_ssl": "0",
                "url": "http://localhost:8000/github/webhook"
            }
        },
        "repository": {
            "id": 123456789,
            "name": "java-login-system",
            "full_name": "your-username/java-login-system",
            "clone_url": "https://github.com/your-username/java-login-system.git"
        }
    }


def test_github_webhook(
    base_url: str = "http://localhost:8000",
    webhook_secret: str = "your_default_secret_token"
):
    """
    测试 GitHub webhook 端点。
    
    参数:
        base_url: API 基础 URL
        webhook_secret: webhook 密钥
    """
    webhook_url = f"{base_url}/github/webhook"
    
    print("=== GitHub Webhook 测试 ===\n")
    
    # 测试 1: Ping 事件
    print("1. 测试 Ping 事件...")
    ping_payload = create_test_ping_payload()
    ping_json = json.dumps(ping_payload)
    ping_signature = create_github_signature(ping_json, webhook_secret)
    
    ping_headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "ping",
        "X-Hub-Signature-256": ping_signature,
        "X-GitHub-Delivery": "test-ping-delivery-123"
    }
    
    try:
        response = requests.post(webhook_url, data=ping_json, headers=ping_headers)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        print("   ✓ Ping 测试完成\n")
    except Exception as e:
        print(f"   ✗ Ping 测试失败: {str(e)}\n")
    
    # 测试 2: Push 事件
    print("2. 测试 Push 事件...")
    push_payload = create_test_push_payload()
    push_json = json.dumps(push_payload)
    push_signature = create_github_signature(push_json, webhook_secret)
    
    push_headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "push",
        "X-Hub-Signature-256": push_signature,
        "X-GitHub-Delivery": "test-push-delivery-456"
    }
    
    try:
        response = requests.post(webhook_url, data=push_json, headers=push_headers)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if "task_id" in result:
                print(f"   ✓ 任务已创建: {result['task_id']}")
                
                # 检查任务状态
                task_id = result['task_id']
                print(f"   检查任务状态: {task_id}")
                
                # 注意：这里需要 API 密钥来查询任务状态
                # 在实际使用中，您需要配置正确的 API 密钥
                
        print("   ✓ Push 测试完成\n")
    except Exception as e:
        print(f"   ✗ Push 测试失败: {str(e)}\n")
    
    # 测试 3: 测试端点
    print("3. 测试测试端点...")
    test_url = f"{base_url}/github/test"
    
    try:
        response = requests.get(test_url)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        print("   ✓ 测试端点测试完成\n")
    except Exception as e:
        print(f"   ✗ 测试端点测试失败: {str(e)}\n")
    
    print("=== 测试完成 ===")


def test_api_endpoints(base_url: str = "http://localhost:8000"):
    """
    测试其他 API 端点。
    
    参数:
        base_url: API 基础 URL
    """
    print("=== API 端点测试 ===\n")
    
    # 测试健康检查
    print("1. 测试健康检查...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        print("   ✓ 健康检查测试完成\n")
    except Exception as e:
        print(f"   ✗ 健康检查测试失败: {str(e)}\n")
    
    # 测试文档
    print("2. 测试 API 文档...")
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"   状态码: {response.status_code}")
        print("   ✓ API 文档可访问\n")
    except Exception as e:
        print(f"   ✗ API 文档测试失败: {str(e)}\n")
    
    print("=== API 端点测试完成 ===")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试 GitHub Webhook API")
    parser.add_argument("--url", default="http://localhost:8000", help="API 基础 URL")
    parser.add_argument("--secret", default="your_default_secret_token", help="Webhook 密钥")
    parser.add_argument("--test-api", action="store_true", help="同时测试其他 API 端点")
    
    args = parser.parse_args()
    
    # 测试 GitHub webhook
    test_github_webhook(args.url, args.secret)
    
    # 如果指定，测试其他 API 端点
    if args.test_api:
        test_api_endpoints(args.url)
