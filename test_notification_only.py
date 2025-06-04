#!/usr/bin/env python3
"""
仅测试通知功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_notification_only():
    """仅测试通知功能"""
    
    print("🔍 测试Lark通知功能")
    print("=" * 40)
    
    try:
        from feishu_notification import send_jacoco_notification
        
        # 测试数据
        webhook_url = "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe"
        repo_url = "http://172.16.1.30/kian/jacocotest.git"
        branch_name = "main"
        commit_id = "84d32a75d4832dc26f33678706bc8446da51cda0"
        
        coverage_data = {
            "line_coverage": 0,
            "branch_coverage": 0,
            "instruction_coverage": 0,
            "method_coverage": 0,
            "class_coverage": 0
        }
        
        scan_result = {
            "status": "no_reports",
            "scan_method": "local",
            "coverage_percentage": 0,
            "lines_covered": 0,
            "lines_total": 0
        }
        
        request_id = "notification_only_test"
        
        print(f"📤 发送通知...")
        print(f"  Webhook URL: {webhook_url[:50]}...")
        print(f"  项目: {repo_url}")
        print(f"  分支: {branch_name}")
        print(f"  提交: {commit_id[:8]}")
        print(f"  覆盖率: {coverage_data}")
        print()
        
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
            
        return result
        
    except Exception as e:
        print(f"❌ 通知测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 独立测试Lark通知功能")
    print("=" * 50)
    
    result = test_notification_only()
    
    print(f"\n📊 测试结果: {'✅ 成功' if result else '❌ 失败'}")
    
    if result:
        print("\n💡 如果通知功能正常，但webhook流程中没有通知，")
        print("   说明问题在于webhook处理流程中的通知调用逻辑")
    else:
        print("\n💡 通知功能本身有问题，需要检查:")
        print("   1. 网络连接")
        print("   2. Lark机器人配置")
        print("   3. Webhook URL是否正确")
