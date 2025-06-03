#!/usr/bin/env python3
"""
简单的 webhook 测试脚本，用于测试你当前使用的简化格式。
"""

import json
import requests


def test_simple_webhook():
    """测试简化格式的 GitLab webhook。"""
    
    url = "http://localhost:8001/github/webhook-no-auth"
    
    # 你当前使用的简化格式
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
        "Content-Type": "application/json",
        "X-Gitlab-Event": "Push Hook"
    }
    
    print("=== 测试简化格式的 GitLab Webhook ===\n")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        print("发送 webhook 请求...")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook 接收成功!")
            print(f"📝 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get('status') == 'accepted':
                task_id = result.get('task_id')
                print(f"\n🎯 任务已排队: {task_id}")
                print(f"请求ID: {result.get('request_id')}")
                
                extracted = result.get('extracted_info', {})
                print(f"\n📋 提取的信息:")
                print(f"  - 仓库: {extracted.get('repo_url')}")
                print(f"  - 提交: {extracted.get('commit_id')}")
                print(f"  - 分支: {extracted.get('branch_name')}")
                print(f"  - 服务: {extracted.get('service_name')}")
                
                print(f"\n⏳ 等待 JaCoCo 扫描完成...")
                print(f"📢 扫描完成后将自动发送飞书通知")
                
                return True
            elif result.get('status') == 'ignored':
                print(f"\n⚠️ Webhook 被忽略: {result.get('message')}")
                if 'available_repos' in result:
                    print(f"可用的仓库配置:")
                    for repo in result['available_repos']:
                        print(f"  - {repo}")
                return False
            else:
                print(f"\n❌ 处理错误: {result.get('message')}")
                return False
        else:
            print("❌ Webhook 请求失败")
            try:
                error = response.json()
                print(f"错误: {json.dumps(error, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误: {response.text}")
            return False
                
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False


def test_with_complete_url():
    """测试包含完整URL的格式。"""
    
    url = "http://localhost:8001/github/webhook-no-auth"
    
    # 包含完整URL的格式
    payload = {
        "object_kind": "push",
        "ref": "refs/heads/develop",
        "user_name": "Kian",
        "project": {
            "name": "jacocoTest",
            "http_url": "https://gitlab.complexdevops.com/kian/jacocoTest.git"
        },
        "commits": [{
            "id": "abc123def456",
            "message": "Fix login bug"
        }]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Gitlab-Event": "Push Hook"
    }
    
    print("\n=== 测试包含完整URL的格式 ===\n")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        print("发送 webhook 请求...")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook 接收成功!")
            print(f"📝 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get('status') == 'accepted':
                print(f"\n🎯 任务已排队: {result.get('task_id')}")
                return True
            else:
                print(f"\n⚠️ 处理结果: {result.get('message')}")
                return False
        else:
            print("❌ Webhook 请求失败")
            print(f"错误: {response.text}")
            return False
                
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False


def main():
    """主函数。"""
    
    print("========================================")
    print("简化格式 GitLab Webhook 测试")
    print("========================================")
    
    # 测试简化格式
    result1 = test_simple_webhook()
    
    # 测试完整格式
    result2 = test_with_complete_url()
    
    print("\n========================================")
    print("测试结果总结")
    print("========================================")
    print(f"简化格式: {'✅ 成功' if result1 else '❌ 失败'}")
    print(f"完整格式: {'✅ 成功' if result2 else '❌ 失败'}")
    print("========================================")
    
    if result1 or result2:
        print("\n🎉 至少一种格式测试成功!")
        print("📋 说明:")
        print("  - 修复了 GitLab URL 构造逻辑")
        print("  - 支持简化格式的 payload")
        print("  - 自动识别 jacocoTest 项目")
        print("\n📱 飞书通知:")
        print("  https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe")
    else:
        print("\n⚠️ 所有格式都失败了")
        print("请检查:")
        print("  1. 服务是否在运行 (http://localhost:8001)")
        print("  2. 配置是否正确")
        print("  3. 日志中的错误信息")


if __name__ == "__main__":
    main()
