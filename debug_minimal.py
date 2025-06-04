#!/usr/bin/env python3
"""
最小化调试脚本 - 直接调用扫描函数并查看详细输出
"""

import sys
import os
import logging

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_minimal_scan():
    """最小化测试扫描和通知"""
    
    print("🔍 最小化调试测试")
    print("=" * 50)
    
    try:
        # 导入必要的模块
        from jacoco_tasks import run_docker_jacoco_scan
        from config import get_service_config
        
        # 测试参数
        repo_url = "http://172.16.1.30/kian/jacocotest.git"
        commit_id = "84d32a75d4832dc26f33678706bc8446da51cda0"
        branch_name = "main"
        request_id = "minimal_debug_001"
        
        print(f"📋 测试参数:")
        print(f"  仓库: {repo_url}")
        print(f"  提交: {commit_id}")
        print(f"  分支: {branch_name}")
        print(f"  请求ID: {request_id}")
        print()
        
        # 获取服务配置
        service_config = get_service_config(repo_url)
        
        print(f"📋 服务配置:")
        for key, value in service_config.items():
            if key == 'notification_webhook':
                print(f"  {key}: {value[:50]}..." if len(str(value)) > 50 else f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")
        print()
        
        # 检查关键配置
        webhook_url = service_config.get('notification_webhook')
        print(f"🔔 通知配置检查:")
        print(f"  Webhook URL存在: {'✅' if webhook_url else '❌'}")
        print(f"  Webhook URL长度: {len(webhook_url) if webhook_url else 0}")
        print(f"  Webhook URL格式: {'✅' if webhook_url and webhook_url.startswith('http') else '❌'}")
        print()
        
        print("🚀 开始扫描...")
        print("-" * 30)
        
        # 直接调用扫描函数
        result = run_docker_jacoco_scan(
            repo_url=repo_url,
            commit_id=commit_id,
            branch_name=branch_name,
            service_config=service_config,
            request_id=request_id
        )
        
        print("-" * 30)
        print("✅ 扫描完成！")
        print()
        
        print("📊 扫描结果:")
        print("-" * 20)
        for key, value in result.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        
        print()
        print("📱 通知相关结果:")
        print("-" * 20)
        notification_keys = [
            'notification_sent', 
            'notification_error', 
            'notification_skip_reason',
            'coverage_summary'
        ]
        
        for key in notification_keys:
            if key in result:
                value = result[key]
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for sub_key, sub_value in value.items():
                        print(f"    {sub_key}: {sub_value}")
                else:
                    print(f"  {key}: {value}")
            else:
                print(f"  {key}: ❌ 未设置")
        
        # 分析结果
        print()
        print("🔍 结果分析:")
        print("-" * 20)
        
        notification_sent = result.get('notification_sent', False)
        if notification_sent:
            print("✅ 通知发送成功")
        else:
            print("❌ 通知未发送")
            
            # 分析原因
            if 'notification_error' in result:
                print(f"  错误原因: {result['notification_error']}")
            elif 'notification_skip_reason' in result:
                print(f"  跳过原因: {result['notification_skip_reason']}")
            else:
                print("  原因未知")
        
        coverage_summary = result.get('coverage_summary')
        if coverage_summary:
            print(f"✅ 覆盖率数据存在: {coverage_summary}")
        else:
            print("❌ 覆盖率数据不存在")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_notification_directly():
    """直接测试通知函数"""
    
    print("\n🧪 直接测试通知函数")
    print("=" * 50)
    
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
        
        request_id = "direct_notification_test"
        
        print("📤 发送通知...")
        print(f"  Webhook URL: {webhook_url[:50]}...")
        print(f"  覆盖率数据: {coverage_data}")
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
            print("✅ 直接通知测试成功")
        else:
            print("❌ 直接通知测试失败")
            
        return result
        
    except Exception as e:
        print(f"❌ 直接通知测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 最小化调试 - 定位通知问题")
    print("=" * 60)
    
    # 测试扫描
    scan_result = test_minimal_scan()
    
    # 测试通知
    notification_result = test_notification_directly()
    
    print("\n📊 调试总结:")
    print("=" * 30)
    print(f"扫描测试: {'✅' if scan_result else '❌'}")
    print(f"通知测试: {'✅' if notification_result else '❌'}")
    
    if scan_result and not scan_result.get('notification_sent', False):
        print("\n🔍 问题分析:")
        print("- 扫描功能正常")
        print("- 通知功能单独测试正常")
        print("- 但扫描过程中通知未发送")
        print("- 可能是扫描过程中的通知调用有问题")
        
        print("\n💡 建议:")
        print("1. 检查扫描过程中的日志")
        print("2. 确认coverage_summary是否正确创建")
        print("3. 确认通知函数是否被正确调用")
    elif scan_result and scan_result.get('notification_sent', False):
        print("\n🎉 问题已解决！")
        print("- 扫描和通知都正常工作")
    else:
        print("\n⚠️ 需要进一步调试")
        print("- 请检查错误日志")
