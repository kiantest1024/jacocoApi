#!/usr/bin/env python3
"""
调试webhook通知流程
"""

import requests
import json
import time

def test_webhook_with_debug():
    """测试webhook并查看详细的通知调试信息"""
    
    print("🔍 调试Webhook通知流程")
    print("=" * 60)
    
    # 测试数据
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
            "message": "Test notification debug"
        }]
    }
    
    url = "http://localhost:8002/github/webhook-no-auth"
    
    print(f"📋 发送webhook到: {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        print("⏳ 发送请求...")
        start_time = time.time()
        
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=600  # 10分钟超时
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ 请求耗时: {duration:.2f} 秒")
        print(f"📊 状态码: {response.status_code}")
        
        try:
            result = response.json()
            print(f"📄 响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 分析结果
            status = result.get('status', 'unknown')
            
            print(f"\n📈 扫描结果分析:")
            print(f"  状态: {status}")
            
            if status == 'completed':
                print("✅ 扫描成功完成！")
                
                # 检查覆盖率信息
                if 'coverage_percentage' in result:
                    print(f"  📈 行覆盖率: {result.get('coverage_percentage', 'N/A')}%")
                    print(f"  🌿 分支覆盖率: {result.get('branch_coverage', 'N/A')}%")
                    print(f"  📊 覆盖行数: {result.get('lines_covered', 'N/A')}/{result.get('lines_total', 'N/A')}")
                
                # 检查是否有coverage_summary
                if 'coverage_summary' in result:
                    print(f"  📋 Coverage Summary: {result['coverage_summary']}")
                else:
                    print("  ❌ 未找到coverage_summary")
                
                # 检查通知相关的信息
                print(f"\n📱 通知相关信息:")
                notification_keys = ['notification_sent', 'notification_error', 'webhook_url']
                for key in notification_keys:
                    if key in result:
                        print(f"  {key}: {result[key]}")
                
            elif status == 'error':
                print(f"❌ 扫描失败: {result.get('message', 'Unknown error')}")
                
        except json.JSONDecodeError:
            print(f"📄 响应文本: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - 请确保服务正在运行")
        print("💡 启动服务: python3 app.py")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def check_service_logs():
    """提示检查服务日志"""
    
    print(f"\n📋 检查服务日志:")
    print("请在服务运行的终端中查找以下关键日志:")
    print("1. [req_xxx] 检查通知配置: webhook_url=...")
    print("2. [req_xxx] report_data keys: [...]")
    print("3. [req_xxx] final_result keys: [...]")
    print("4. [req_xxx] 从xxx获取coverage_summary")
    print("5. [req_xxx] 准备发送飞书通知...")
    print("6. [req_xxx] 飞书通知已发送")
    print()
    print("如果没有看到这些日志，说明通知逻辑没有被执行")
    print("如果看到了但没有'飞书通知已发送'，说明通知发送失败")

def suggest_debug_steps():
    """建议调试步骤"""
    
    print(f"\n🔧 调试建议:")
    print("1. 确保服务正在运行: python3 app.py")
    print("2. 发送webhook: python3 debug_webhook_notification.py")
    print("3. 查看服务日志中的通知相关信息")
    print("4. 如果没有通知日志，检查配置文件中的notification_webhook")
    print("5. 如果有通知日志但发送失败，检查网络连接")
    print()
    print("💡 常见问题:")
    print("- 配置文件中notification_webhook为空")
    print("- coverage_summary数据结构不正确")
    print("- 网络连接问题")
    print("- Lark机器人权限问题")

if __name__ == "__main__":
    test_webhook_with_debug()
    check_service_logs()
    suggest_debug_steps()
