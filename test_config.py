#!/usr/bin/env python3
"""
配置验证脚本
"""

def test_config():
    print("🔧 测试配置...")
    
    try:
        from config import LARK_CONFIG, get_service_config
        print("✅ 配置导入成功")
        
        # 测试全局Lark配置
        webhook_url = LARK_CONFIG.get("webhook_url")
        if webhook_url:
            print(f"✅ 全局Lark Webhook: {webhook_url[:50]}...")
        else:
            print("❌ 未配置全局Lark Webhook")
        
        # 测试服务配置
        test_repo = "https://gitlab.complexdevops.com/kian/jacocoTest.git"
        service_config = get_service_config(test_repo)
        
        print(f"✅ 服务配置生成成功:")
        print(f"   - 服务名称: {service_config.get('service_name')}")
        print(f"   - 通知Webhook: {service_config.get('notification_webhook', 'N/A')[:50]}...")
        print(f"   - 扫描方法: {service_config.get('scan_method')}")
        print(f"   - 强制本地扫描: {service_config.get('force_local_scan')}")
        
        # 测试Lark通知模块
        from lark_notification import LarkNotifier, send_jacoco_notification
        print("✅ Lark通知模块导入成功")
        
        # 创建通知器实例
        notifier = LarkNotifier()
        print(f"✅ Lark通知器创建成功，使用Webhook: {notifier.webhook_url[:50]}...")
        
        print("\n🎉 所有配置测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_config()
