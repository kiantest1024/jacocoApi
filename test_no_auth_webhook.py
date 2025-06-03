#!/usr/bin/env python3
"""
测试无认证 webhook 端点。
"""

import json
import requests


def test_no_auth_webhook():
    """测试无认证的 webhook 端点。"""
    
    url = "http://localhost:8001/github/webhook-no-auth"
    
    # 您的原始 GitLab payload
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
    
    print("=== 测试无认证 GitLab Webhook ===\n")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 成功!")
            print(f"📝 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 检查关键信息
            if result.get('status') == 'accepted':
                print(f"\n🎉 Webhook 处理成功!")
                print(f"任务 ID: {result.get('task_id')}")
                print(f"事件类型: {result.get('event_type')}")
                
                extracted = result.get('extracted_info', {})
                print(f"提取的信息:")
                print(f"  - 仓库: {extracted.get('repo_url')}")
                print(f"  - 提交: {extracted.get('commit_id')}")
                print(f"  - 分支: {extracted.get('branch_name')}")
                print(f"  - 服务: {extracted.get('service_name')}")
                
            elif result.get('status') == 'ignored':
                print(f"\n⚠️ Webhook 被忽略: {result.get('message')}")
                if 'available_repos' in result:
                    print(f"可用的仓库配置: {result['available_repos']}")
                    
            elif result.get('status') == 'error':
                print(f"\n❌ 处理错误: {result.get('message')}")
                if 'extracted' in result:
                    print(f"提取的信息: {result['extracted']}")
        else:
            print("❌ 失败")
            try:
                error = response.json()
                print(f"错误: {json.dumps(error, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - 请确保服务在运行")
    except Exception as e:
        print(f"❌ 异常: {str(e)}")


if __name__ == "__main__":
    test_no_auth_webhook()
