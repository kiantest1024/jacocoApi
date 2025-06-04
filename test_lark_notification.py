#!/usr/bin/env python3
"""
测试Lark通知功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feishu_notification import send_jacoco_notification

def test_lark_notification():
    """测试Lark通知发送"""
    
    print("🧪 测试Lark通知功能")
    print("=" * 50)
    
    # 测试数据
    webhook_url = "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe"
    repo_url = "http://172.16.1.30/kian/jacocotest.git"
    branch_name = "main"
    commit_id = "84d32a75d4832dc26f33678706bc8446da51cda0"
    
    # 模拟覆盖率数据
    coverage_data = {
        "line_coverage": 85.71,
        "branch_coverage": 75.00,
        "instruction_coverage": 80.50,
        "method_coverage": 90.00,
        "class_coverage": 100.00
    }
    
    # 模拟扫描结果
    scan_result = {
        "status": "success",
        "scan_method": "local",
        "coverage_percentage": 85.71,
        "lines_covered": 12,
        "lines_total": 14,
        "branches_covered": 3,
        "branches_total": 4
    }
    
    request_id = "test_notification_001"
    
    print(f"📋 测试参数:")
    print(f"  Webhook URL: {webhook_url}")
    print(f"  仓库: {repo_url}")
    print(f"  分支: {branch_name}")
    print(f"  提交: {commit_id}")
    print(f"  行覆盖率: {coverage_data['line_coverage']}%")
    print(f"  分支覆盖率: {coverage_data['branch_coverage']}%")
    print()
    
    try:
        print("📤 发送Lark通知...")
        
        send_jacoco_notification(
            webhook_url=webhook_url,
            repo_url=repo_url,
            branch_name=branch_name,
            commit_id=commit_id,
            coverage_data=coverage_data,
            scan_result=scan_result,
            request_id=request_id
        )
        
        print("✅ Lark通知发送成功！")
        print()
        print("💡 请检查Lark群组是否收到通知消息")
        
        return True
        
    except Exception as e:
        print(f"❌ Lark通知发送失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_notification():
    """测试错误通知"""
    
    print("\n🧪 测试错误通知功能")
    print("=" * 50)
    
    from feishu_notification import send_error_notification
    
    webhook_url = "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe"
    repo_url = "http://172.16.1.30/kian/jacocotest.git"
    error_message = "这是一个测试错误消息"
    service_name = "JaCoCo测试服务"
    
    try:
        print("📤 发送错误通知...")
        
        send_error_notification(
            webhook_url=webhook_url,
            repo_url=repo_url,
            error_message=error_message,
            service_name=service_name
        )
        
        print("✅ 错误通知发送成功！")
        return True
        
    except Exception as e:
        print(f"❌ 错误通知发送失败: {e}")
        return False

def check_config():
    """检查配置"""
    
    print("🔍 检查配置文件...")
    
    try:
        from config import config
        
        webhook_url = config.get('notification_webhook')
        if webhook_url:
            print(f"✅ 配置中的Webhook URL: {webhook_url}")
        else:
            print("❌ 配置中未找到notification_webhook")
        
        use_docker = config.get('use_docker', True)
        force_local_scan = config.get('force_local_scan', False)
        
        print(f"📋 扫描配置:")
        print(f"  use_docker: {use_docker}")
        print(f"  force_local_scan: {force_local_scan}")
        
        if force_local_scan or not use_docker:
            print("✅ 配置为本地扫描模式")
        else:
            print("⚠️ 配置为Docker扫描模式")
        
    except Exception as e:
        print(f"❌ 检查配置失败: {e}")

if __name__ == "__main__":
    print("🔍 Lark通知功能测试")
    print("=" * 60)
    
    # 检查配置
    check_config()
    print()
    
    # 测试成功通知
    success1 = test_lark_notification()
    
    # 测试错误通知
    success2 = test_error_notification()
    
    print("\n📊 测试结果:")
    print(f"  成功通知: {'✅' if success1 else '❌'}")
    print(f"  错误通知: {'✅' if success2 else '❌'}")
    
    if success1 and success2:
        print("\n🎉 所有通知测试通过！")
    else:
        print("\n⚠️ 部分通知测试失败，请检查网络连接和Webhook URL")
