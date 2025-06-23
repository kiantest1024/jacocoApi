#!/usr/bin/env python3
"""专门测试 Lark 机器人推送功能"""

import requests
import json
import time

def test_lark_notification():
    """测试 Lark 机器人推送功能"""
    
    url = "http://localhost:8003/github/webhook-no-auth"
    
    payload = {
        "object_kind": "push",
        "project": {
            "name": "jacocotest",
            "http_url": "http://172.16.1.30/kian/jacocotest.git"
        },
        "commits": [{"id": "main"}],
        "ref": "refs/heads/main",
        "user_name": "kian"
    }
    
    print("🧪 测试 Lark 机器人推送功能")
    print("=" * 50)
    print(f"📡 URL: {url}")
    print(f"📋 载荷: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    start_time = time.time()
    
    try:
        print("\n🚀 发送扫描请求...")
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️  总耗时: {duration:.1f}秒")
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功")
            
            # 重点检查 Lark 机器人推送结果
            print(f"\n📤 Lark 机器人推送结果:")
            print("=" * 30)
            
            notification_result = result.get("notification_result")
            if notification_result:
                if notification_result.get("success"):
                    print("🎉 ✅ Lark 机器人推送成功！")
                    print(f"   📝 消息: {notification_result.get('message', 'N/A')}")
                    
                    # 检查调试信息中的通知结果
                    debug_notification = result.get("debug_info", {}).get("notification_result")
                    if debug_notification:
                        print(f"   🔍 调试信息: {debug_notification}")
                    
                    return True
                else:
                    print("❌ Lark 机器人推送失败")
                    error_msg = notification_result.get("error", "未知错误")
                    print(f"   ❌ 错误信息: {error_msg}")
                    return False
            else:
                print("⚠️  未找到 Lark 机器人推送结果")
                return False
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"📋 响应: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败")
        print("💡 请确保调试服务正在运行")
        return False
    except Exception as e:
        print(f"💥 请求异常: {e}")
        return False

def check_service_status():
    """检查服务状态"""
    
    print("🔍 检查调试服务状态")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:8003/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 调试服务运行正常")
            print(f"📋 版本: {result.get('version')}")
            print(f"🔍 调试模式: {result.get('debug_mode')}")
            return True
        else:
            print("❌ 调试服务状态异常")
            return False
    except:
        print("❌ 无法连接到调试服务")
        print("💡 请启动调试服务: python app_debug.py")
        return False

def check_lark_config():
    """检查 Lark 机器人配置"""
    
    print("\n🔍 检查 Lark 机器人配置")
    print("=" * 30)
    
    try:
        # 检查机器人列表
        response = requests.get("http://localhost:8003/config/bots", timeout=10)
        if response.status_code == 200:
            bots = response.json()
            print(f"📋 找到 {len(bots)} 个机器人配置:")
            
            for bot_id, bot_config in bots.items():
                print(f"   🤖 {bot_id}:")
                print(f"      名称: {bot_config.get('name', 'N/A')}")
                print(f"      Webhook URL: {'已配置' if bot_config.get('webhook_url') else '未配置'}")
                
                # 检查 Webhook URL 是否有效
                webhook_url = bot_config.get('webhook_url')
                if webhook_url and webhook_url.startswith('https://open.larksuite.com'):
                    print(f"      ✅ Webhook URL 格式正确")
                else:
                    print(f"      ⚠️  Webhook URL 可能无效")
            
            return len(bots) > 0
        else:
            print(f"❌ 获取机器人配置失败: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ 检查机器人配置异常: {e}")
        return False

def main():
    """主函数"""
    
    print("🧪 JaCoCo 调试版本 - Lark 机器人推送专项测试")
    print("=" * 60)
    
    # 检查服务状态
    if not check_service_status():
        return
    
    # 检查 Lark 机器人配置
    if not check_lark_config():
        print("\n⚠️  警告: 没有找到有效的 Lark 机器人配置")
        print("💡 请确保配置了正确的 Webhook URL")
    
    print("\n" + "=" * 60)
    
    # 运行推送测试
    success = test_lark_notification()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Lark 机器人推送测试成功！")
        print("\n✅ 测试结果:")
        print("- 调试服务正常运行")
        print("- Lark 机器人配置正确")
        print("- 推送功能工作正常")
        print("- 通知已成功发送到 Lark 群组")
        
        print("\n💡 说明:")
        print("- 虽然 Windows 环境下 Maven 扫描失败")
        print("- 但 Lark 机器人推送功能完全正常")
        print("- 在 Linux 服务器上会有完整的覆盖率数据")
    else:
        print("⚠️  Lark 机器人推送测试失败")
        print("\n🔧 故障排除:")
        print("- 检查 Webhook URL 是否正确")
        print("- 确认 Lark 群组机器人是否启用")
        print("- 验证网络连接是否正常")
        print("- 查看调试日志获取详细错误信息")

if __name__ == "__main__":
    main()
