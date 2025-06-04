#!/usr/bin/env python3
"""
JaCoCo API Webhook测试脚本
"""

import requests
import json
import time

def test_webhook():
    """测试webhook功能"""
    
    print("🔍 测试JaCoCo API Webhook")
    print("=" * 50)
    
    # GitLab webhook数据
    payload = {
        "object_kind": "push",
        "ref": "refs/heads/main",
        "user_name": "kian",
        "project": {
            "name": "jacocotest",
            "http_url": "http://172.16.1.30/kian/jacocotest.git"
        },
        "commits": [{
            "id": "84d32a75d4832dc26f33678706bc8446da51cda0",
            "message": "Test webhook"
        }]
    }
    
    url = "http://localhost:8002/github/webhook-no-auth"
    
    print(f"📤 发送webhook到: {url}")
    print(f"📦 项目: {payload['project']['name']}")
    print(f"🌿 分支: {payload['ref']}")
    print(f"📝 提交: {payload['commits'][0]['id'][:8]}")
    print()
    
    try:
        print("⏳ 发送请求...")
        start_time = time.time()
        
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ 请求耗时: {duration:.2f} 秒")
        print(f"📊 HTTP状态码: {response.status_code}")
        print()
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("📄 API响应:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print()
                
                # 分析响应
                status = result.get('status', 'unknown')
                print(f"📊 状态: {status}")
                
                if status == 'completed':
                    print("✅ 扫描已完成（同步模式）")
                    
                    # 检查通知状态
                    notification_sent = result.get('notification_sent', False)
                    if notification_sent:
                        print("✅ Lark通知已发送")
                    else:
                        print("❌ Lark通知未发送")
                        
                    # 检查覆盖率
                    coverage = result.get('coverage_percentage', 'N/A')
                    print(f"📈 覆盖率: {coverage}%")
                    
                elif status == 'accepted':
                    print("⏳ 任务已排队（异步模式）")
                    task_id = result.get('task_id', 'N/A')
                    print(f"📋 任务ID: {task_id}")
                    
                elif status == 'error':
                    print("❌ 扫描失败")
                    message = result.get('message', 'Unknown error')
                    print(f"📄 错误信息: {message}")
                    
            except json.JSONDecodeError:
                print(f"📄 响应文本: {response.text}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"📄 响应: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败")
        print("💡 请确保JaCoCo API服务正在运行: python3 app.py")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def test_lark_notification():
    """测试Lark通知功能"""
    
    print("\n🔍 测试Lark通知功能")
    print("=" * 50)
    
    try:
        from feishu_notification import send_jacoco_notification
        
        # 测试数据
        webhook_url = "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe"
        repo_url = "http://172.16.1.30/kian/jacocotest.git"
        branch_name = "main"
        commit_id = "84d32a75d4832dc26f33678706bc8446da51cda0"
        
        coverage_data = {
            "line_coverage": 85.71,
            "branch_coverage": 75.00,
            "instruction_coverage": 80.50,
            "method_coverage": 90.00,
            "class_coverage": 100.00
        }
        
        scan_result = {
            "status": "success",
            "scan_method": "local",
            "coverage_percentage": 85.71
        }
        
        request_id = "test_notification"
        
        print("📤 发送测试通知...")
        result = send_jacoco_notification(
            webhook_url=webhook_url,
            repo_url=repo_url,
            branch_name=branch_name,
            commit_id=commit_id,
            coverage_data=coverage_data,
            scan_result=scan_result,
            request_id=request_id
        )
        
        if result:
            print("✅ 通知发送成功")
            print("💡 请检查Lark群组是否收到消息")
        else:
            print("❌ 通知发送失败")
            
    except Exception as e:
        print(f"❌ 通知测试失败: {e}")

def check_service():
    """检查服务状态"""
    
    print("🔍 检查JaCoCo API服务")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            print("✅ JaCoCo API服务正常")
            return True
        else:
            print(f"⚠️ 服务状态异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ JaCoCo API服务未启动")
        print("💡 请先启动服务: python3 app.py")
        return False
    except Exception as e:
        print(f"❌ 检查服务失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 JaCoCo API 功能测试")
    print("=" * 60)
    
    if check_service():
        print()
        test_webhook()
        test_lark_notification()
        
        print("\n💡 测试完成")
        print("如果webhook测试成功但没有收到Lark通知，请检查:")
        print("1. 服务端日志中的通知相关信息")
        print("2. Lark机器人配置是否正确")
        print("3. 网络连接是否正常")
    else:
        print("\n💡 请先启动JaCoCo API服务，然后重新运行此测试")
