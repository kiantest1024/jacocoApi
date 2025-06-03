#!/usr/bin/env python3
"""
测试 GitHub 格式的 webhook。
"""

import json
import requests


def test_github_format():
    """测试 GitHub 格式的 webhook。"""
    
    url = "http://localhost:8001/github/webhook"
    
    # GitHub 格式的 payload
    payload = {
        "ref": "refs/heads/develop",
        "repository": {
            "name": "jacocoTest",
            "clone_url": "https://gitlab.com/user/jacocoTest.git",  # 使用您的实际仓库
            "ssh_url": "git@gitlab.com:user/jacocoTest.git"
        },
        "commits": [{
            "id": "abc123def456",
            "message": "Fix login bug"
        }],
        "after": "abc123def456"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "push"
    }
    
    print("测试 GitHub 格式的 webhook...")
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


def test_github_ping():
    """测试 GitHub ping 事件。"""
    
    url = "http://localhost:8001/github/webhook"
    
    # GitHub ping 格式
    payload = {
        "zen": "Non-blocking is better than blocking.",
        "hook_id": 12345,
        "repository": {
            "name": "jacocoTest",
            "clone_url": "https://gitlab.com/user/jacocoTest.git"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "ping"
    }
    
    print("测试 GitHub ping 事件...")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            print("✓ Ping 成功")
        else:
            print("✗ Ping 失败")
            
    except Exception as e:
        print(f"✗ 异常: {str(e)}")


if __name__ == "__main__":
    print("=== GitHub 格式 Webhook 测试 ===\n")
    
    # 测试 ping
    test_github_ping()
    print()
    
    # 测试 push
    test_github_format()
