#!/usr/bin/env python3
"""测试调试版本的 Lark 机器人推送功能"""

import requests
import json
import time

def test_debug_scan_with_notification():
    """测试调试版本扫描并验证 Lark 机器人推送"""
    
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
    
    print("🧪 测试调试版本 - 包含 Lark 机器人推送")
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
            timeout=180  # 3分钟超时
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️  总耗时: {duration:.1f}秒")
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功")
            
            # 显示基本信息
            print(f"📋 状态: {result.get('status', 'unknown')}")
            print(f"🔍 扫描方法: {result.get('debug_info', {}).get('scan_method', 'unknown')}")
            print(f"💬 消息: {result.get('message', 'no message')}")
            
            # 显示扫描分析
            if "debug_info" in result and "scan_analysis" in result["debug_info"]:
                analysis = result["debug_info"]["scan_analysis"]
                print(f"\n📊 扫描分析:")
                print(f"   测试运行: {analysis.get('tests_run', 0)}")
                print(f"   测试失败: {analysis.get('tests_failed', 0)}")
                print(f"   编译错误: {len(analysis.get('compilation_errors', []))}")
            
            # 显示覆盖率信息
            if "report_data" in result and "coverage_summary" in result["report_data"]:
                coverage = result["report_data"]["coverage_summary"]
                print(f"\n📈 覆盖率统计:")
                print(f"   指令覆盖率: {coverage.get('instruction_coverage', 0):.2f}%")
                print(f"   分支覆盖率: {coverage.get('branch_coverage', 0):.2f}%")
                print(f"   行覆盖率: {coverage.get('line_coverage', 0):.2f}%")
                print(f"   方法覆盖率: {coverage.get('method_coverage', 0):.2f}%")
                print(f"   类覆盖率: {coverage.get('class_coverage', 0):.2f}%")
            
            # 显示报告链接
            if "report_data" in result and "html_report_url" in result["report_data"]:
                html_url = result["report_data"]["html_report_url"]
                print(f"\n🔗 HTML 报告: {html_url}")
            
            # 重点检查 Lark 机器人推送结果
            print(f"\n📤 Lark 机器人推送结果:")
            print("=" * 30)
            
            notification_result = result.get("notification_result")
            if notification_result:
                if notification_result.get("success"):
                    print("✅ Lark 机器人推送成功")
                    
                    # 显示推送详情
                    if "details" in notification_result:
                        details = notification_result["details"]
                        print(f"   推送的机器人数量: {details.get('bots_count', 0)}")
                        print(f"   成功推送数量: {details.get('success_count', 0)}")
                        print(f"   失败推送数量: {details.get('failed_count', 0)}")
                        
                        if details.get("failed_bots"):
                            print(f"   失败的机器人: {details['failed_bots']}")
                    
                    if "message" in notification_result:
                        print(f"   推送消息: {notification_result['message']}")
                        
                else:
                    print("❌ Lark 机器人推送失败")
                    error_msg = notification_result.get("error", "未知错误")
                    print(f"   错误信息: {error_msg}")
                    
                    # 显示详细错误
                    if "details" in notification_result:
                        details = notification_result["details"]
                        print(f"   详细信息: {details}")
            else:
                print("⚠️  未找到 Lark 机器人推送结果")
                print("   可能原因:")
                print("   - 通知功能未启用")
                print("   - 没有配置对应的机器人")
                print("   - 通知模块导入失败")
            
            # 显示调试信息中的通知结果
            debug_notification = result.get("debug_info", {}).get("notification_result")
            if debug_notification and debug_notification != notification_result:
                print(f"\n🔍 调试信息中的通知结果:")
                print(f"   {debug_notification}")
            
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"📋 响应: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时 (3分钟)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败")
        print("💡 请确保调试服务正在运行")
        return False
    except Exception as e:
        print(f"💥 请求异常: {e}")
        return False

def check_lark_bot_config():
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
                print(f"      描述: {bot_config.get('description', 'N/A')}")
                print(f"      Webhook URL: {'已配置' if bot_config.get('webhook_url') else '未配置'}")
                print(f"      自定义: {bot_config.get('is_custom', False)}")
        else:
            print(f"❌ 获取机器人配置失败: {response.status_code}")
    
    except Exception as e:
        print(f"❌ 检查机器人配置异常: {e}")
    
    try:
        # 检查项目映射
        response = requests.get("http://localhost:8003/config/mappings", timeout=10)
        if response.status_code == 200:
            mappings = response.json()
            print(f"\n📋 找到 {len(mappings)} 个项目映射:")
            
            for mapping in mappings:
                print(f"   📁 {mapping.get('project_name', 'N/A')}:")
                print(f"      机器人: {mapping.get('bot_id', 'N/A')}")
                print(f"      Git URL: {mapping.get('git_url', 'N/A')}")
        else:
            print(f"❌ 获取项目映射失败: {response.status_code}")
    
    except Exception as e:
        print(f"❌ 检查项目映射异常: {e}")

def main():
    """主函数"""
    
    print("🧪 JaCoCo 调试版本 - Lark 机器人推送测试")
    print("=" * 50)
    
    # 检查服务状态
    try:
        response = requests.get("http://localhost:8003/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 调试服务运行正常")
            print(f"📋 版本: {result.get('version')}")
            print(f"🔍 调试模式: {result.get('debug_mode')}")
        else:
            print("❌ 调试服务状态异常")
            return
    except:
        print("❌ 无法连接到调试服务")
        print("💡 请启动调试服务: python app_debug.py")
        return
    
    # 检查 Lark 机器人配置
    check_lark_bot_config()
    
    print("\n" + "=" * 50)
    
    # 运行测试
    success = test_debug_scan_with_notification()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 测试完成！")
        print("\n💡 分析要点:")
        print("- 检查扫描是否成功完成")
        print("- 验证覆盖率数据是否正确")
        print("- 确认 Lark 机器人推送状态")
        print("- 查看推送失败的具体原因")
    else:
        print("⚠️  测试遇到问题。")
    
    print("\n🔧 故障排除:")
    print("- 如果通知推送失败，检查机器人配置")
    print("- 确认项目映射是否正确")
    print("- 验证 Webhook URL 是否可访问")
    print("- 查看调试日志获取详细错误信息")

if __name__ == "__main__":
    main()
