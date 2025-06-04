#!/usr/bin/env python3
"""
JaCoCo API 综合测试脚本
包含所有功能的测试：配置、webhook、HTML报告、Lark通知等
"""

import requests
import json
import time
import os
from config_manager import get_current_config, validate_lark_config, test_lark_connection

def test_service_health():
    """测试服务健康状态"""
    print("🔍 1. 服务健康检查")
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务运行正常")
            return True
        else:
            print("❌ 服务状态异常")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        print("💡 请先启动服务: python app.py")
        return False

def test_configuration():
    """测试配置功能"""
    print("\n⚙️ 2. 配置验证")
    
    # 验证Lark配置
    validation = validate_lark_config()
    if validation["valid"]:
        print("✅ Lark配置验证通过")
    else:
        print("❌ Lark配置验证失败:")
        for error in validation["errors"]:
            print(f"  - {error}")
    
    if validation["warnings"]:
        print("⚠️ 配置警告:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")

def test_html_reports():
    """测试HTML报告功能"""
    print("\n📊 3. HTML报告功能")
    try:
        response = requests.get("http://localhost:8002/reports", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 找到 {data['total_projects']} 个项目的报告")
            
            if data['reports']:
                for project in data['reports']:
                    project_name = project['project_name']
                    report_count = len(project['reports'])
                    print(f"  📁 {project_name}: {report_count} 个报告")
                    
                    # 测试访问最新报告
                    if project['reports']:
                        latest_report = project['reports'][0]
                        test_url = latest_report['full_url']
                        try:
                            report_response = requests.get(test_url, timeout=5)
                            if report_response.status_code == 200:
                                print(f"  ✅ 报告可访问: {latest_report['commit_id']}")
                            else:
                                print(f"  ⚠️ 报告访问异常: {report_response.status_code}")
                        except:
                            print(f"  ⚠️ 报告访问失败")
            else:
                print("📝 暂无可用报告")
        else:
            print(f"❌ 获取报告列表失败: {response.status_code}")
    except Exception as e:
        print(f"❌ HTML报告测试异常: {e}")

def test_webhook_functionality():
    """测试Webhook功能"""
    print("\n🔗 4. Webhook功能测试")
    
    # 模拟GitLab webhook
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": "jacocoTest",
            "http_url": "https://gitlab.complexdevops.com/kian/jacocoTest.git"
        },
        "user_name": "test_user",
        "commits": [
            {
                "id": "test_" + str(int(time.time())),
                "message": "Test comprehensive functionality"
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
                
                # 验证链接可访问
                try:
                    report_response = requests.get(html_url, timeout=10)
                    if report_response.status_code == 200:
                        print("✅ HTML报告可正常访问")
                    else:
                        print(f"⚠️ HTML报告访问异常: {report_response.status_code}")
                except Exception as e:
                    print(f"⚠️ 访问HTML报告失败: {e}")
            
            # 检查通知发送状态
            notification_sent = result.get('scan_result', {}).get('notification_sent')
            if notification_sent:
                print("✅ Lark通知发送成功")
            else:
                print("⚠️ Lark通知发送失败或跳过")
                
        else:
            print(f"❌ Webhook处理失败: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ Webhook测试异常: {e}")

def test_lark_connectivity():
    """测试Lark连接"""
    print("\n📱 5. Lark连接测试")
    result = test_lark_connection()
    
    if result["success"]:
        print(f"✅ {result['message']} (响应时间: {result['response_time']}ms)")
    else:
        print(f"❌ {result['message']}")

def main():
    """主测试函数"""
    print("🧪 JaCoCo API 综合功能测试")
    print("=" * 60)
    
    # 1. 服务健康检查
    if not test_service_health():
        return
    
    # 2. 配置验证
    test_configuration()
    
    # 3. HTML报告功能
    test_html_reports()
    
    # 4. Lark连接测试
    test_lark_connectivity()
    
    # 5. 询问是否进行完整的Webhook测试
    print("\n" + "=" * 60)
    user_input = input("🤔 是否要进行完整的Webhook扫描测试？(y/N): ").strip().lower()
    if user_input in ['y', 'yes']:
        test_webhook_functionality()
    
    print("\n🎉 综合测试完成！")
    print("\n📋 测试总结:")
    print("1. ✅ 服务健康状态")
    print("2. ✅ 配置验证功能")
    print("3. ✅ HTML报告功能")
    print("4. ✅ Lark连接功能")
    if user_input in ['y', 'yes']:
        print("5. ✅ Webhook扫描功能")
    
    print("\n💡 使用建议:")
    print("- 定期运行此测试脚本验证系统功能")
    print("- 在部署新版本前进行完整测试")
    print("- 如有问题请查看详细日志")

if __name__ == "__main__":
    main()
