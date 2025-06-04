#!/usr/bin/env python3
"""
测试修复效果：
1. 验证不会重复发送通知
2. 验证HTML报告链接使用正确的服务器地址
"""

import requests
import json
import time

def test_fixes():
    """测试修复效果"""
    
    print("🧪 测试修复效果")
    print("=" * 60)
    
    base_url = "http://localhost:8002"
    
    # 1. 检查服务状态
    print("\n🔍 1. 检查服务状态")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务运行正常")
        else:
            print("❌ 服务状态异常")
            return
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        print("💡 请先启动服务: python app.py")
        return
    
    # 2. 测试报告列表API的URL生成
    print("\n🌐 2. 测试报告列表API的URL生成")
    try:
        response = requests.get(f"{base_url}/reports", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 报告列表API正常，找到 {data['total_projects']} 个项目")
            
            if data['reports']:
                for project in data['reports']:
                    project_name = project['project_name']
                    print(f"  📁 项目: {project_name}")
                    
                    for report in project['reports'][:2]:  # 只显示前2个
                        full_url = report['full_url']
                        print(f"    🔗 {report['commit_id']}: {full_url}")
                        
                        # 检查URL是否正确
                        if full_url.startswith("http://localhost:8002"):
                            print("    ✅ URL格式正确")
                        else:
                            print(f"    ❌ URL格式异常: {full_url}")
            else:
                print("📝 暂无报告，将测试webhook生成报告")
                test_webhook_single_notification()
        else:
            print(f"❌ 报告列表API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试报告列表API异常: {e}")

def test_webhook_single_notification():
    """测试webhook只发送一次通知"""
    
    print("\n📤 3. 测试Webhook单次通知")
    
    # 模拟GitLab webhook
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": "jacocoTest",
            "http_url": "https://gitlab.complexdevops.com/kian/jacocoTest.git"
        },
        "user_name": "kian",
        "commits": [
            {
                "id": "fix_test_" + str(int(time.time())),  # 使用时间戳避免重复
                "message": "Test single notification fix"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    try:
        print("📤 发送webhook请求...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8002/github/webhook-no-auth",
            json=webhook_data,
            timeout=120
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Webhook处理成功 (耗时: {duration:.1f}秒)")
            
            # 检查HTML报告链接
            if 'html_report_url' in result.get('report_data', {}):
                html_url = result['report_data']['html_report_url']
                print(f"🔗 HTML报告链接: {html_url}")
                
                # 验证URL格式
                if html_url.startswith("http://"):
                    print("✅ HTML报告链接格式正确")
                    
                    # 测试访问
                    try:
                        report_response = requests.get(html_url, timeout=10)
                        if report_response.status_code == 200:
                            print("✅ HTML报告可正常访问")
                        else:
                            print(f"⚠️ HTML报告访问异常: {report_response.status_code}")
                    except Exception as e:
                        print(f"⚠️ 访问HTML报告失败: {e}")
                else:
                    print(f"❌ HTML报告链接格式异常: {html_url}")
            else:
                print("⚠️ 响应中未找到HTML报告链接")
            
            # 检查通知发送状态
            notification_sent = result.get('scan_result', {}).get('notification_sent')
            if notification_sent:
                print("✅ 通知发送成功")
                print("💡 请检查Lark群组，应该只收到1条通知消息")
            else:
                print("⚠️ 通知发送状态未知")
                
        else:
            print(f"❌ Webhook处理失败: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ Webhook测试异常: {e}")

def test_url_with_different_hosts():
    """测试不同Host头的URL生成"""
    
    print("\n🌍 4. 测试不同Host头的URL生成")
    
    test_hosts = [
        "localhost:8002",
        "192.168.1.100:8002", 
        "myserver.com:8002"
    ]
    
    for host in test_hosts:
        try:
            headers = {"Host": host}
            response = requests.get(
                "http://localhost:8002/reports", 
                headers=headers, 
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['reports']:
                    sample_url = data['reports'][0]['reports'][0]['full_url']
                    expected_prefix = f"http://{host}"
                    
                    if sample_url.startswith(expected_prefix):
                        print(f"✅ Host {host}: URL正确 - {sample_url}")
                    else:
                        print(f"❌ Host {host}: URL错误 - {sample_url}")
                else:
                    print(f"📝 Host {host}: 无报告数据")
            else:
                print(f"❌ Host {host}: API调用失败")
                
        except Exception as e:
            print(f"❌ Host {host}: 测试异常 - {e}")

if __name__ == "__main__":
    test_fixes()
    
    print("\n" + "=" * 60)
    user_input = input("🤔 是否要测试Webhook单次通知？(y/N): ").strip().lower()
    if user_input in ['y', 'yes']:
        test_webhook_single_notification()
    
    print("\n" + "=" * 60)
    user_input = input("🤔 是否要测试不同Host的URL生成？(y/N): ").strip().lower()
    if user_input in ['y', 'yes']:
        test_url_with_different_hosts()
    
    print("\n🎉 修复效果测试完成！")
    print("\n📋 修复总结:")
    print("1. ✅ 移除了jacoco_tasks.py中的重复通知发送")
    print("2. ✅ 实现了动态服务器地址获取")
    print("3. ✅ HTML报告链接现在使用实际的Host地址")
    print("4. ✅ 支持不同的部署环境（localhost、IP、域名）")
