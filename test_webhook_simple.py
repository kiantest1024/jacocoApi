#!/usr/bin/env python3
"""
简单的webhook测试脚本 - 模拟GitLab推送触发JaCoCo扫描
"""

import requests
import json
import time

def test_webhook_trigger():
    """测试webhook触发扫描"""
    
    print("🔍 测试Webhook触发JaCoCo扫描")
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
            "message": "Test webhook trigger for JaCoCo scan"
        }]
    }
    
    url = "http://localhost:8002/github/webhook-no-auth"
    
    print(f"📤 发送webhook到: {url}")
    print(f"📦 项目: {payload['project']['name']}")
    print(f"🌿 分支: {payload['ref']}")
    print(f"📝 提交: {payload['commits'][0]['id'][:8]}")
    print()
    
    try:
        print("⏳ 发送webhook请求...")
        start_time = time.time()
        
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5分钟超时
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
                analyze_response(result)
                
            except json.JSONDecodeError:
                print(f"📄 响应文本: {response.text}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"📄 响应: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
        print("💡 扫描可能需要更长时间，请检查服务端日志")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败")
        print("💡 请确保JaCoCo API服务正在运行: python3 app.py")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def analyze_response(result):
    """分析API响应"""
    
    print("📈 响应分析:")
    print("-" * 30)
    
    status = result.get('status', 'unknown')
    print(f"📊 状态: {status}")
    
    if status == 'completed':
        print("✅ 扫描已完成（同步模式）")
        
        # 检查通知状态
        notification_sent = result.get('notification_sent', False)
        notification_error = result.get('notification_error')
        notification_skip_reason = result.get('notification_skip_reason')
        
        print(f"📱 通知状态:")
        if notification_sent:
            print(f"  ✅ Lark通知已发送")
        elif notification_error:
            print(f"  ❌ 通知发送失败: {notification_error}")
        elif notification_skip_reason:
            print(f"  ⚠️ 通知被跳过: {notification_skip_reason}")
        else:
            print(f"  ❓ 通知状态未知")
        
        # 检查覆盖率
        coverage_percentage = result.get('coverage_percentage', 'N/A')
        branch_coverage = result.get('branch_coverage', 'N/A')
        print(f"📈 覆盖率:")
        print(f"  行覆盖率: {coverage_percentage}%")
        print(f"  分支覆盖率: {branch_coverage}%")
        
    elif status == 'accepted':
        print("⏳ 任务已排队（异步模式）")
        task_id = result.get('task_id', 'N/A')
        print(f"📋 任务ID: {task_id}")
        print("💡 请检查服务端日志查看扫描进度")
        
    elif status == 'error':
        print("❌ 扫描失败")
        message = result.get('message', 'Unknown error')
        print(f"📄 错误信息: {message}")
        
    else:
        print(f"❓ 未知状态: {status}")

def check_service():
    """检查服务状态"""
    
    print("🔍 检查JaCoCo API服务")
    print("=" * 50)
    
    try:
        # 检查健康状态
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            print("✅ JaCoCo API服务正常")
        else:
            print(f"⚠️ 服务状态异常: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ JaCoCo API服务未启动")
        print("💡 请先启动服务: python3 app.py")
        return False
    except Exception as e:
        print(f"❌ 检查服务失败: {e}")
        return False
    
    try:
        # 检查测试端点
        response = requests.get("http://localhost:8002/github/test", timeout=5)
        if response.status_code == 200:
            print("✅ Webhook端点正常")
        else:
            print(f"⚠️ Webhook端点异常: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Webhook端点检查失败: {e}")
    
    return True

def show_instructions():
    """显示使用说明"""
    
    print("📋 使用说明")
    print("=" * 50)
    print("1. 确保JaCoCo API服务正在运行")
    print("   启动命令: python3 app.py")
    print()
    print("2. 运行此测试脚本")
    print("   测试命令: python3 test_webhook_simple.py")
    print()
    print("3. 查看服务端日志")
    print("   重点关注包含以下内容的日志:")
    print("   - [req_xxx] 使用同步模式执行扫描")
    print("   - [req_xxx] ==================== 通知调试开始")
    print("   - [req_xxx] ✅ 开始发送飞书通知")
    print("   - [req_xxx] ✅ 飞书通知发送成功")
    print()
    print("4. 检查Lark群组")
    print("   如果通知发送成功，应该能在Lark群组中看到消息")
    print()

if __name__ == "__main__":
    show_instructions()
    
    if check_service():
        print()
        test_webhook_trigger()
        
        print("\n💡 调试提示:")
        print("如果没有收到Lark通知，请:")
        print("1. 检查服务端日志中的通知相关信息")
        print("2. 确认是否看到 '✅ 飞书通知发送成功' 日志")
        print("3. 如果看到发送成功但Lark没收到，可能是网络问题")
        print("4. 如果没看到发送日志，可能是通知逻辑没有执行")
    else:
        print("\n💡 请先启动JaCoCo API服务，然后重新运行此测试")
