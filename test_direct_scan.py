#!/usr/bin/env python3
"""
直接测试扫描函数，绕过webhook和Celery
"""

import sys
import os
import tempfile

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jacoco_tasks import run_docker_jacoco_scan
from config import get_service_config

def test_direct_scan():
    """直接测试扫描函数"""
    
    print("🧪 直接测试JaCoCo扫描函数")
    print("=" * 60)
    
    # 测试参数
    repo_url = "http://172.16.1.30/kian/jacocotest.git"
    commit_id = "84d32a75d4832dc26f33678706bc8446da51cda0"
    branch_name = "main"
    request_id = "direct_test_001"
    
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
        print(f"  {key}: {value}")
    print()
    
    # 检查通知配置
    webhook_url = service_config.get('notification_webhook')
    print(f"🔔 通知配置:")
    print(f"  Webhook URL: {webhook_url}")
    print(f"  URL长度: {len(webhook_url) if webhook_url else 0}")
    print(f"  URL有效: {'✅' if webhook_url and webhook_url.startswith('http') else '❌'}")
    print()
    
    try:
        print("🚀 开始直接扫描...")
        
        # 直接调用扫描函数（不通过Celery）
        result = run_docker_jacoco_scan(
            repo_url=repo_url,
            commit_id=commit_id,
            branch_name=branch_name,
            service_config=service_config,
            request_id=request_id
        )
        
        print("✅ 扫描完成！")
        print()
        print("📊 扫描结果:")
        for key, value in result.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        
        # 检查通知相关的结果
        print()
        print("📱 通知相关结果:")
        notification_keys = ['notification_sent', 'notification_error', 'notification_skip_reason']
        for key in notification_keys:
            if key in result:
                print(f"  {key}: {result[key]}")
            else:
                print(f"  {key}: 未设置")
        
        # 检查覆盖率数据
        print()
        print("📈 覆盖率数据:")
        coverage_keys = ['coverage_percentage', 'line_coverage', 'branch_coverage', 'coverage_summary']
        for key in coverage_keys:
            if key in result:
                print(f"  {key}: {result[key]}")
            else:
                print(f"  {key}: 未找到")
        
        return result
        
    except Exception as e:
        print(f"❌ 扫描失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_notification_function():
    """直接测试通知函数"""
    
    print("\n🧪 直接测试通知函数")
    print("=" * 60)
    
    try:
        from feishu_notification import send_jacoco_notification
        
        # 模拟数据
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
            "coverage_percentage": 85.71,
            "lines_covered": 12,
            "lines_total": 14
        }
        
        request_id = "direct_notification_test"
        
        print("📤 发送通知...")
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
        else:
            print("❌ 通知发送失败")
            
        return result
        
    except Exception as e:
        print(f"❌ 通知测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 直接测试JaCoCo扫描和通知")
    print("=" * 80)
    
    # 测试扫描
    scan_result = test_direct_scan()
    
    # 测试通知
    notification_result = test_notification_function()
    
    print("\n📊 测试总结:")
    print(f"  扫描测试: {'✅' if scan_result else '❌'}")
    print(f"  通知测试: {'✅' if notification_result else '❌'}")
    
    if scan_result and notification_result:
        print("\n🎉 所有测试通过！")
        print("如果webhook仍然不发送通知，问题可能在于:")
        print("1. Celery任务队列配置")
        print("2. 异步执行中的异常处理")
        print("3. 日志级别设置")
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
