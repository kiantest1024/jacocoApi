#!/usr/bin/env python3
"""
测试 GitLab ComplexDevOps 仓库的 JaCoCo 扫描功能。
"""

import json
import requests
import time


def test_gitlab_webhook():
    """测试 GitLab webhook 功能。"""
    
    url = "http://localhost:8001/github/webhook-no-auth"
    
    # GitLab ComplexDevOps webhook payload (完整格式)
    payload = {
        "object_kind": "push",
        "ref": "refs/heads/main",
        "user_name": "kian",
        "project": {
            "name": "jacocoTest",
            "http_url": "https://gitlab.complexdevops.com/kian/jacocoTest.git",
            "ssh_url": "git@gitlab.complexdevops.com:kian/jacocoTest.git",
            "web_url": "https://gitlab.complexdevops.com/kian/jacocoTest"
        },
        "commits": [{
            "id": "main",
            "message": "Test JaCoCo coverage scan",
            "author": {
                "name": "Kian",
                "email": "kian@complexdevops.com"
            }
        }],
        "after": "main",
        "before": "000000000000",
        "checkout_sha": "main"
    }

    # 也测试简化格式（你当前使用的格式）
    simple_payload = {
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
    
    print("=== 测试 GitLab ComplexDevOps Webhook ===\n")
    print(f"URL: {url}")
    print(f"仓库: https://gitlab.complexdevops.com/kian/jacocoTest.git")
    print()

    # 首先测试简化格式（你当前使用的格式）
    print("🧪 测试简化格式的 payload...")
    try:
        print("发送简化 webhook 请求...")
        response = requests.post(url, json=simple_payload, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ 简化格式 Webhook 接收成功!")
            print(f"📝 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

            if result.get('status') == 'accepted':
                print(f"\n🎯 简化格式测试成功，任务已排队: {result.get('task_id')}")
            else:
                print(f"\n⚠️ 简化格式被忽略: {result.get('message')}")
        else:
            print("❌ 简化格式 Webhook 请求失败")
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"❌ 简化格式测试异常: {str(e)}")

    print("\n" + "="*50 + "\n")

    # 然后测试完整格式
    print("🧪 测试完整格式的 payload...")
    try:
        print("发送完整 webhook 请求...")
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
                print(f"📢 扫描完成后将自动发送飞书通知到:")
                print(f"   https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe")
                
                return True
            elif result.get('status') == 'ignored':
                print(f"\n⚠️ Webhook 被忽略: {result.get('message')}")
                if 'available_repos' in result:
                    print(f"可用的仓库配置: {result['available_repos']}")
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


def test_feishu_notification():
    """测试飞书通知功能。"""
    
    print("\n=== 测试飞书通知功能 ===\n")
    
    try:
        from feishu_notification import FeishuNotifier
        
        # 飞书 webhook URL
        webhook_url = "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe"
        
        # 创建通知器
        notifier = FeishuNotifier(webhook_url)
        
        # 模拟覆盖率数据
        coverage_data = {
            "line_coverage": 75.5,
            "branch_coverage": 68.2,
            "instruction_coverage": 72.8,
            "method_coverage": 80.1,
            "class_coverage": 85.0
        }
        
        # 模拟扫描结果
        scan_result = {
            "status": "success",
            "reports_dir": "./reports/test",
            "scan_method": "docker"
        }
        
        print("发送测试通知到飞书...")
        success = notifier.send_jacoco_report(
            repo_url="https://gitlab.complexdevops.com/kian/jacocoTest.git",
            branch_name="main",
            commit_id="test123456",
            coverage_data=coverage_data,
            scan_result=scan_result,
            request_id="test_notification"
        )
        
        if success:
            print("✅ 飞书通知发送成功!")
            print("📱 请检查飞书群聊是否收到消息")
            return True
        else:
            print("❌ 飞书通知发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试飞书通知异常: {str(e)}")
        return False


def check_service_status():
    """检查服务状态。"""
    
    print("=== 检查服务状态 ===\n")
    
    try:
        # 健康检查
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print("✅ 服务正在运行")
            print(f"📝 版本: {result.get('version', 'unknown')}")
            print(f"📝 状态: {result.get('status', 'unknown')}")
            print(f"📝 时间: {result.get('timestamp', 'unknown')}")
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


def check_docker_image():
    """检查 Docker 镜像。"""
    
    print("\n=== 检查 Docker 镜像 ===\n")
    
    import subprocess
    
    try:
        result = subprocess.run(
            ['docker', 'images', 'jacoco-scanner'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and 'jacoco-scanner' in result.stdout:
            print("✅ JaCoCo 扫描器 Docker 镜像存在")
            print(result.stdout)
            return True
        else:
            print("❌ JaCoCo 扫描器 Docker 镜像不存在")
            print("请运行以下命令构建镜像:")
            print("docker build -t jacoco-scanner:latest -f docker/Dockerfile.jacoco-scanner .")
            return False
            
    except Exception as e:
        print(f"❌ 检查 Docker 镜像失败: {str(e)}")
        return False


def main():
    """主函数。"""
    
    print("========================================")
    print("GitLab ComplexDevOps JaCoCo 测试")
    print("========================================")
    
    # 1. 检查服务状态
    service_ok = check_service_status()
    
    if not service_ok:
        print("\n❌ 服务未运行，请先启动服务")
        return
    
    # 2. 检查 Docker 镜像
    docker_ok = check_docker_image()
    
    # 3. 测试飞书通知
    feishu_ok = test_feishu_notification()
    
    # 4. 测试 GitLab webhook
    webhook_ok = test_gitlab_webhook()
    
    print("\n========================================")
    print("测试结果总结")
    print("========================================")
    print(f"服务状态: {'✅' if service_ok else '❌'}")
    print(f"Docker 镜像: {'✅' if docker_ok else '❌'}")
    print(f"飞书通知: {'✅' if feishu_ok else '❌'}")
    print(f"GitLab Webhook: {'✅' if webhook_ok else '❌'}")
    print("========================================")
    
    if all([service_ok, docker_ok, webhook_ok]):
        print("\n🎉 所有功能测试通过!")
        print("📋 功能说明:")
        print("  - ✅ 支持 GitLab ComplexDevOps 仓库")
        print("  - ✅ 增量更新 (首次 clone，后续 git pull)")
        print("  - ✅ 飞书机器人通知")
        print("  - ✅ JaCoCo 覆盖率报告生成")
        print("\n📱 配置的飞书机器人:")
        print("  https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe")
    else:
        print("\n⚠️ 部分功能需要修复")


if __name__ == "__main__":
    main()
