#!/usr/bin/env python3
"""测试本地扫描功能"""

import requests
import json
import time

def test_local_scan():
    """测试强制本地扫描"""
    
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
    
    print("🧪 测试强制本地扫描")
    print("=" * 40)
    print("💡 调试版本已配置为跳过Docker，直接使用本地扫描")
    print(f"📡 URL: {url}")
    
    start_time = time.time()
    
    try:
        print("\n🚀 发送扫描请求...")
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2分钟超时
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️  总耗时: {duration:.1f}秒")
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功")
            
            # 显示关键信息
            print(f"📋 状态: {result.get('status', 'unknown')}")
            print(f"🔍 扫描方法: {result.get('debug_info', {}).get('scan_method', 'unknown')}")
            print(f"💬 消息: {result.get('message', 'no message')}")
            
            # 显示扫描分析
            if "debug_info" in result and "scan_analysis" in result["debug_info"]:
                analysis = result["debug_info"]["scan_analysis"]
                print(f"\n📊 扫描分析:")
                print(f"   测试运行: {analysis.get('tests_run', 0)}")
                print(f"   测试失败: {analysis.get('tests_failed', 0)}")
                print(f"   测试错误: {analysis.get('tests_errors', 0)}")
                print(f"   编译错误: {len(analysis.get('compilation_errors', []))}")
                
                # 显示编译错误详情
                if analysis.get('compilation_errors'):
                    print(f"\n🔴 编译错误:")
                    for error in analysis['compilation_errors'][:5]:  # 只显示前5个
                        print(f"   {error}")
            
            # 显示报告信息
            if "report_data" in result:
                report_data = result["report_data"]
                print(f"\n📋 报告状态:")
                print(f"   报告可用: {report_data.get('reports_available', False)}")
                print(f"   XML报告: {report_data.get('xml_report_path', 'N/A')}")
                print(f"   HTML报告: {report_data.get('html_report_available', False)}")
            
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"📋 响应: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时 (2分钟)")
        print("💡 本地扫描也超时，可能是项目或环境问题")
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
    try:
        response = requests.get("http://localhost:8003/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 调试服务运行正常")
            print(f"📋 版本: {result.get('version')}")
            print(f"🔍 调试模式: {result.get('debug_mode')}")
            return True
        else:
            print(f"❌ 服务状态异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        return False

def main():
    """主函数"""
    print("🧪 JaCoCo 本地扫描测试")
    print("=" * 40)
    
    # 检查服务状态
    if not check_service_status():
        print("💡 请启动调试服务: python app_debug.py")
        return
    
    print("\n" + "=" * 40)
    
    # 运行测试
    success = test_local_scan()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 本地扫描测试完成！")
        print("💡 如果仍有问题，可能是:")
        print("   - Maven 未安装或配置错误")
        print("   - Git 仓库访问问题")
        print("   - 项目代码编译错误")
    else:
        print("⚠️  本地扫描测试失败")
        print("💡 建议检查:")
        print("   - 服务器是否安装了 Maven 和 Git")
        print("   - 网络是否能访问 Git 仓库")
        print("   - 查看调试日志获取详细错误信息")

if __name__ == "__main__":
    main()
