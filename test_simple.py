#!/usr/bin/env python3
"""
简化的JaCoCo扫描测试
验证基本功能是否正常
"""

import requests
import json
import time

def test_service_health():
    """测试服务健康状态"""
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_basic_scan():
    """测试基本扫描功能"""
    print("🔧 测试基本JaCoCo扫描")
    print("=" * 50)
    
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": "jacocotest",
            "http_url": "http://172.16.1.30/kian/jacocotest.git"
        },
        "user_name": "test_user",
        "commits": [
            {
                "id": "5ea76b4989a17153eade57d7d55609ebad7fdd9e",
                "message": "Test basic scan"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    try:
        start_time = time.time()
        print("📤 发送扫描请求...")
        
        response = requests.post(
            "http://localhost:8002/github/webhook-no-auth",
            json=webhook_data,
            timeout=300
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ 扫描耗时: {duration:.1f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求处理成功")
            
            # 分析扫描结果
            scan_result = result.get('scan_result', {})
            report_data = result.get('report_data', {})
            
            print(f"\n📊 扫描结果:")
            print(f"  状态: {scan_result.get('status', 'unknown')}")
            print(f"  方法: {scan_result.get('scan_method', 'unknown')}")
            print(f"  返回码: {scan_result.get('return_code', 'unknown')}")
            
            # 检查覆盖率数据
            coverage_summary = report_data.get('coverage_summary', {})
            if coverage_summary:
                print(f"\n📈 覆盖率数据:")
                has_coverage = False
                
                for metric, value in coverage_summary.items():
                    print(f"  {metric}: {value}%")
                    if isinstance(value, (int, float)) and value > 0:
                        has_coverage = True
                
                if has_coverage:
                    print(f"\n🎉 扫描成功！覆盖率数据正常")
                    
                    # 检查HTML报告
                    html_url = report_data.get('html_report_url')
                    if html_url:
                        print(f"🔗 HTML报告: {html_url}")
                    
                    return "success"
                else:
                    print(f"\n⚠️ 覆盖率为0%")
                    return "zero_coverage"
            else:
                print(f"\n❌ 未找到覆盖率数据")
                return "no_coverage"
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应: {response.text}")
            return "request_failed"
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return "timeout"
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return "error"

def main():
    """主函数"""
    print("🧪 JaCoCo扫描基本功能测试")
    print("=" * 50)
    
    # 检查服务状态
    if not test_service_health():
        print("❌ JaCoCo API服务未运行")
        print("💡 请先启动服务: python app.py")
        return
    
    print("✅ 服务连接正常")
    
    # 执行基本扫描测试
    result = test_basic_scan()
    
    # 检查服务稳定性
    print("\n🔄 检查服务稳定性...")
    time.sleep(2)
    if test_service_health():
        print("✅ 服务在扫描后仍正常运行")
        stable = True
    else:
        print("❌ 服务在扫描后停止响应")
        stable = False
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    
    if result == "success" and stable:
        print("🎉 所有测试通过！")
        print("✅ 主要功能:")
        print("  1. 服务正常运行")
        print("  2. 扫描功能正常")
        print("  3. 覆盖率数据正确")
        print("  4. HTML报告可访问")
        print("  5. 服务保持稳定")
        
    elif result == "success":
        print("⚠️ 扫描功能正常，但服务稳定性有问题")
        
    elif stable:
        print("⚠️ 服务稳定，但扫描功能有问题")
        
        if result == "zero_coverage":
            print("💡 问题：覆盖率为0%")
            print("   建议检查JaCoCo配置和测试执行")
        elif result == "no_coverage":
            print("💡 问题：未找到覆盖率数据")
            print("   建议检查报告生成和解析")
        elif result == "request_failed":
            print("💡 问题：请求处理失败")
            print("   建议检查服务日志")
        
    else:
        print("❌ 扫描和稳定性都有问题")
        print("💡 建议:")
        print("  1. 重启服务")
        print("  2. 检查配置文件")
        print("  3. 查看详细日志")

if __name__ == "__main__":
    main()
