#!/usr/bin/env python3
"""
简单的 webhook 测试脚本。
"""

import json
import requests


def test_simple_gitlab_webhook():
    """测试简单的 GitLab webhook（无签名验证）。"""
    
    url = "http://localhost:8001/github/webhook"
    
    # 您的原始 payload
    payload = {
        "object_kind": "push",
        "ref": "refs/heads/develop",
        "user_name": "Kian",
        "project": {"name": "jacocoTest"},
        "commits": [{
            "id": "abc123def456",
            "message": "Fix login bug"
        }]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("测试 GitLab webhook...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 成功: {result.get('message', '')}")
            if result.get('task_id'):
                print(f"任务 ID: {result['task_id']}")
        else:
            print("✗ 失败")
            
    except Exception as e:
        print(f"✗ 异常: {str(e)}")


def test_health():
    """测试健康检查端点。"""
    
    url = "http://localhost:8001/health"
    
    print("测试健康检查...")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            print("✓ 服务正常运行")
        else:
            print("✗ 服务异常")
            
    except Exception as e:
        print(f"✗ 连接失败: {str(e)}")


if __name__ == "__main__":
    print("=== 简单 Webhook 测试 ===\n")
    
    # 先测试健康检查
    test_health()
    print()
    
    # 再测试 webhook
    test_simple_gitlab_webhook()
