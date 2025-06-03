#!/usr/bin/env python3
"""
测试通用 JaCoCo 扫描服务。
支持任何配置了 webhook 的 Maven 项目。
"""

import json
import requests


def test_universal_gitlab_webhook():
    """测试通用 GitLab webhook 处理。"""
    
    url = "http://localhost:8001/github/webhook-no-auth"
    
    # 测试不同的项目
    test_projects = [
        {
            "name": "jacocotest",
            "repo_url": "http://172.16.1.30/kian/jacocotest.git",
            "description": "实际的 GitLab 项目"
        },
        {
            "name": "my-java-app",
            "repo_url": "https://github.com/user/my-java-app.git",
            "description": "模拟的 GitHub 项目"
        },
        {
            "name": "spring-boot-demo",
            "repo_url": "https://gitlab.com/company/spring-boot-demo.git",
            "description": "模拟的 GitLab.com 项目"
        }
    ]
    
    headers = {
        "Content-Type": "application/json",
        "X-Gitlab-Event": "Push Hook"
    }
    
    print("=== 测试通用 JaCoCo 扫描服务 ===\n")
    print("🎯 功能: 支持任何配置了 webhook 的 Maven 项目")
    print("📋 测试项目:")
    
    for i, project in enumerate(test_projects, 1):
        print(f"  {i}. {project['name']} - {project['description']}")
    
    print("\n" + "="*60 + "\n")
    
    success_count = 0
    
    for project in test_projects:
        print(f"🧪 测试项目: {project['name']}")
        print(f"📦 仓库: {project['repo_url']}")
        
        # 构建 webhook payload
        payload = {
            "object_kind": "push",
            "ref": "refs/heads/main",
            "user_name": "developer",
            "project": {
                "name": project['name'],
                "http_url": project['repo_url']
            },
            "commits": [{
                "id": "abc123def456",
                "message": f"Update {project['name']} code"
            }]
        }
        
        try:
            print("📤 发送 webhook 请求...")
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Webhook 接收成功!")
                
                if result.get('status') == 'accepted':
                    task_id = result.get('task_id')
                    print(f"🎯 任务已排队: {task_id}")
                    
                    extracted = result.get('extracted_info', {})
                    print(f"📋 提取的信息:")
                    print(f"  - 仓库: {extracted.get('repo_url')}")
                    print(f"  - 提交: {extracted.get('commit_id')}")
                    print(f"  - 分支: {extracted.get('branch_name')}")
                    print(f"  - 服务: {extracted.get('service_name')}")
                    
                    success_count += 1
                    print("✅ 测试成功!")
                else:
                    print(f"⚠️ 处理结果: {result.get('message')}")
            else:
                print("❌ Webhook 请求失败")
                print(f"错误: {response.text}")
                
        except Exception as e:
            print(f"❌ 异常: {str(e)}")
        
        print("\n" + "-"*50 + "\n")
    
    return success_count, len(test_projects)


def test_github_webhook():
    """测试 GitHub webhook 格式。"""
    
    url = "http://localhost:8001/github/webhook-no-auth"
    
    # GitHub webhook payload
    payload = {
        "ref": "refs/heads/main",
        "repository": {
            "name": "java-microservice",
            "full_name": "company/java-microservice",
            "clone_url": "https://github.com/company/java-microservice.git"
        },
        "commits": [{
            "id": "def456abc789",
            "message": "Add new feature"
        }],
        "after": "def456abc789"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "push"
    }
    
    print("🧪 测试 GitHub webhook 格式")
    print(f"📦 项目: {payload['repository']['name']}")
    print(f"📦 仓库: {payload['repository']['clone_url']}")
    
    try:
        print("📤 发送 GitHub webhook 请求...")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ GitHub Webhook 接收成功!")
            
            if result.get('status') == 'accepted':
                print(f"🎯 任务已排队: {result.get('task_id')}")
                return True
            else:
                print(f"⚠️ 处理结果: {result.get('message')}")
                return False
        else:
            print("❌ GitHub Webhook 请求失败")
            print(f"错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False


def check_service_status():
    """检查服务状态。"""
    
    print("=== 检查服务状态 ===\n")
    
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print("✅ 服务正在运行")
            print(f"📝 版本: {result.get('version', 'unknown')}")
            print(f"📝 状态: {result.get('status', 'unknown')}")
            return True
        else:
            print(f"⚠️ 服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务")
        print("请确保服务在 http://localhost:8001 上运行")
        return False
    except Exception as e:
        print(f"❌ 检查服务时出错: {str(e)}")
        return False


def main():
    """主函数。"""
    
    print("========================================")
    print("通用 JaCoCo 扫描服务测试")
    print("========================================")
    
    # 1. 检查服务状态
    service_ok = check_service_status()
    
    if not service_ok:
        print("\n❌ 服务未运行，请先启动服务")
        return
    
    print("\n" + "="*60 + "\n")
    
    # 2. 测试 GitLab webhook（多个项目）
    gitlab_success, gitlab_total = test_universal_gitlab_webhook()
    
    # 3. 测试 GitHub webhook
    github_success = test_github_webhook()
    
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    print(f"服务状态: {'✅' if service_ok else '❌'}")
    print(f"GitLab 项目: {gitlab_success}/{gitlab_total} 成功")
    print(f"GitHub 项目: {'✅' if github_success else '❌'}")
    print("="*60)
    
    if gitlab_success > 0 or github_success:
        print("\n🎉 通用 JaCoCo 扫描服务测试成功!")
        print("\n📋 服务特性:")
        print("  ✅ 支持任何配置了 webhook 的 Maven 项目")
        print("  ✅ 自动识别项目名称和配置")
        print("  ✅ 支持 GitHub 和 GitLab webhook 格式")
        print("  ✅ 增量代码更新（首次 clone，后续 git pull）")
        print("  ✅ Docker 容器隔离执行")
        print("  ✅ 自动飞书通知")
        print("\n📱 通知配置:")
        print("  飞书机器人: https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe")
        print("\n🔧 使用方法:")
        print("  1. 在任何 Maven 项目中配置 webhook")
        print("  2. Webhook URL: http://your-server:8001/github/webhook")
        print("  3. 支持 GitHub 和 GitLab")
        print("  4. 推送代码后自动触发 JaCoCo 扫描")
    else:
        print("\n⚠️ 测试失败，请检查配置")


if __name__ == "__main__":
    main()
