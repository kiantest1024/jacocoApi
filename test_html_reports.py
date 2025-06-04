#!/usr/bin/env python3
"""
测试HTML报告功能
"""

import requests
import json
import time

def test_html_reports():
    """测试HTML报告功能"""
    
    print("🧪 测试HTML报告功能")
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
    
    # 2. 查看可用报告
    print("\n📊 2. 查看可用的HTML报告")
    try:
        response = requests.get(f"{base_url}/reports", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 找到 {data['total_projects']} 个项目的报告")
            
            if data['reports']:
                for project in data['reports']:
                    project_name = project['project_name']
                    report_count = len(project['reports'])
                    print(f"  📁 {project_name}: {report_count} 个报告")
                    
                    # 显示最新的3个报告
                    for i, report in enumerate(project['reports'][:3]):
                        commit_id = report['commit_id']
                        created_time = report['created_time']
                        full_url = report['full_url']
                        print(f"    🔗 {commit_id} ({created_time})")
                        print(f"       {full_url}")
                        
                        if i == 0:  # 测试访问最新报告
                            print(f"\n🌐 3. 测试访问最新报告")
                            test_report_access(full_url)
            else:
                print("📝 暂无可用报告")
                print("💡 请先触发一次webhook扫描生成报告")
        else:
            print(f"❌ 获取报告列表失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取报告列表异常: {e}")

def test_report_access(report_url):
    """测试报告访问"""
    try:
        response = requests.get(report_url, timeout=10)
        if response.status_code == 200:
            content = response.text
            if "JaCoCo Coverage Report" in content or "jacoco" in content.lower():
                print("✅ HTML报告访问成功，内容正常")
                print(f"📄 报告大小: {len(content)} 字符")
            else:
                print("⚠️ HTML报告访问成功，但内容可能异常")
        else:
            print(f"❌ HTML报告访问失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 访问HTML报告异常: {e}")

def test_webhook_with_html():
    """测试webhook并检查HTML报告生成"""
    
    print("\n🔗 4. 测试Webhook触发HTML报告生成")
    
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
                "id": "test123456",
                "message": "Test HTML report generation"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    try:
        print("📤 发送webhook请求...")
        response = requests.post(
            "http://localhost:8002/github/webhook-no-auth",
            json=webhook_data,
            timeout=120  # 扫描可能需要较长时间
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook处理成功")
            
            if 'html_report_url' in result.get('report_data', {}):
                html_url = result['report_data']['html_report_url']
                print(f"🔗 HTML报告链接: {html_url}")
                
                # 等待一下再测试访问
                print("⏳ 等待报告生成...")
                time.sleep(2)
                test_report_access(html_url)
            else:
                print("⚠️ 响应中未找到HTML报告链接")
        else:
            print(f"❌ Webhook处理失败: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ Webhook测试异常: {e}")

if __name__ == "__main__":
    test_html_reports()
    
    # 询问是否测试webhook
    print("\n" + "=" * 60)
    user_input = input("🤔 是否要测试Webhook触发HTML报告生成？(y/N): ").strip().lower()
    if user_input in ['y', 'yes']:
        test_webhook_with_html()
    
    print("\n🎉 HTML报告功能测试完成！")
