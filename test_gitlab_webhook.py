#!/usr/bin/env python3
"""
GitLab Webhook 测试脚本。
用于测试 GitLab webhook 接口的功能。
"""

import json
import requests
from typing import Dict, Any


def create_gitlab_push_payload() -> Dict[str, Any]:
    """
    创建测试用的 GitLab push 事件负载。
    
    返回:
        测试负载字典
    """
    return {
        "object_kind": "push",
        "ref": "refs/heads/develop",
        "user_name": "Kian",
        "project": {
            "name": "jacocoTest",
            "http_url": "https://gitlab.com/user/jacocoTest.git",
            "ssh_url": "git@gitlab.com:user/jacocoTest.git",
            "web_url": "https://gitlab.com/user/jacocoTest"
        },
        "commits": [{
            "id": "abc123def456",
            "message": "Fix login bug",
            "author": {
                "name": "Kian",
                "email": "kian@example.com"
            }
        }],
        "after": "abc123def456",
        "before": "000000000000",
        "checkout_sha": "abc123def456"
    }


def create_gitlab_merge_request_payload() -> Dict[str, Any]:
    """
    创建测试用的 GitLab merge request 事件负载。
    
    返回:
        测试负载字典
    """
    return {
        "object_kind": "merge_request",
        "user": {
            "name": "Kian",
            "username": "kian",
            "email": "kian@example.com"
        },
        "project": {
            "name": "jacocoTest",
            "http_url": "https://gitlab.com/user/jacocoTest.git",
            "ssh_url": "git@gitlab.com:user/jacocoTest.git",
            "web_url": "https://gitlab.com/user/jacocoTest"
        },
        "object_attributes": {
            "source_branch": "feature-branch",
            "target_branch": "main",
            "state": "opened",
            "last_commit": {
                "id": "def456abc789",
                "message": "Add new feature"
            }
        }
    }


def test_gitlab_webhook(base_url: str = "http://localhost:8001"):
    """
    测试 GitLab webhook 端点。
    
    参数:
        base_url: API 基础 URL
    """
    webhook_url = f"{base_url}/github/webhook"  # 注意：仍使用 /github/webhook 端点
    
    print("=== GitLab Webhook 测试 ===\n")
    
    # 测试 1: GitLab Push 事件
    print("1. 测试 GitLab Push 事件...")
    push_payload = create_gitlab_push_payload()
    
    headers = {
        "Content-Type": "application/json",
        "X-Gitlab-Event": "Push Hook",  # GitLab 特有的头
        "X-Gitlab-Token": "test-token"   # GitLab 特有的头
    }
    
    try:
        response = requests.post(webhook_url, json=push_payload, headers=headers, timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "accepted":
                print("   ✓ GitLab Push 事件处理成功")
                task_id = result.get("task_id")
                if task_id:
                    print(f"   任务 ID: {task_id}")
                    return task_id
            elif result.get("status") == "ignored":
                print("   ℹ GitLab Push 事件被忽略 (可能没有配置对应的仓库)")
                return None
        else:
            print("   ✗ GitLab Push 测试失败")
            return None
    except Exception as e:
        print(f"   ✗ GitLab Push 测试异常: {str(e)}")
        return None
    
    print()
    
    # 测试 2: GitLab Merge Request 事件
    print("2. 测试 GitLab Merge Request 事件...")
    mr_payload = create_gitlab_merge_request_payload()
    
    headers = {
        "Content-Type": "application/json",
        "X-Gitlab-Event": "Merge Request Hook",
        "X-Gitlab-Token": "test-token"
    }
    
    try:
        response = requests.post(webhook_url, json=mr_payload, headers=headers, timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "accepted":
                print("   ✓ GitLab Merge Request 事件处理成功")
            elif result.get("status") == "ignored":
                print("   ℹ GitLab Merge Request 事件被忽略")
        else:
            print("   ✗ GitLab Merge Request 测试失败")
    except Exception as e:
        print(f"   ✗ GitLab Merge Request 测试异常: {str(e)}")
    
    print()


def test_your_original_payload(base_url: str = "http://localhost:8001"):
    """
    测试您原始的 GitLab payload。
    
    参数:
        base_url: API 基础 URL
    """
    webhook_url = f"{base_url}/github/webhook"
    
    print("=== 测试您的原始 GitLab Payload ===\n")
    
    # 您原始的 payload
    original_payload = {
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
        "Content-Type": "application/json",
        "X-Gitlab-Event": "Push Hook"
    }
    
    try:
        response = requests.post(webhook_url, json=original_payload, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 处理成功: {result.get('message', '')}")
            if result.get("status") == "accepted":
                print(f"任务 ID: {result.get('task_id')}")
            elif result.get("status") == "ignored":
                print("事件被忽略，可能需要配置仓库")
        else:
            print("✗ 处理失败")
    except Exception as e:
        print(f"✗ 测试异常: {str(e)}")
    
    print()


def main():
    """主函数。"""
    print("========================================")
    print("GitLab Webhook 测试")
    print("========================================")
    
    # 测试完整的 GitLab webhook
    test_gitlab_webhook()
    
    # 测试您的原始 payload
    test_your_original_payload()
    
    print("========================================")
    print("测试完成")
    print("========================================")
    print("\n如果测试成功，您现在可以:")
    print("1. 配置 GitLab webhook 指向: http://your-server:8001/github/webhook")
    print("2. 设置 Content-Type: application/json")
    print("3. 选择 Push events 和 Merge request events")


if __name__ == "__main__":
    main()
