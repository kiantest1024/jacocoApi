#!/usr/bin/env python3
"""
快速测试Java项目覆盖率
"""

import requests
import json

def quick_test():
    """快速测试Java项目"""
    
    # 测试Java项目
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": "backend-lotto-game",
            "http_url": "http://172.16.1.30/kian/backend-lotto-game.git"
        },
        "user_name": "test_user",
        "commits": [
            {
                "id": "main",
                "message": "Test Java project coverage"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    print("🧪 测试Java项目覆盖率")
    print(f"项目: {webhook_data['project']['name']}")
    print(f"仓库: {webhook_data['project']['http_url']}")
    
    try:
        response = requests.post(
            "http://localhost:8002/github/webhook-no-auth",
            json=webhook_data,
            timeout=600
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook处理成功")
            
            # 分析结果
            scan_result = result.get('scan_result', {})
            report_data = result.get('report_data', {})
            
            print(f"\n📊 扫描结果:")
            print(f"  状态: {scan_result.get('status')}")
            print(f"  方法: {scan_result.get('scan_method')}")
            print(f"  返回码: {scan_result.get('return_code')}")
            
            # 检查Maven输出
            maven_output = scan_result.get('maven_output', '')
            if "BUILD SUCCESS" in maven_output:
                print("✅ Maven构建成功")
            elif "BUILD FAILURE" in maven_output:
                print("❌ Maven构建失败")
            
            if "Tests run:" in maven_output:
                print("✅ 检测到测试执行")
                # 提取测试结果
                for line in maven_output.split('\n'):
                    if "Tests run:" in line:
                        print(f"  {line.strip()}")
            else:
                print("⚠️ 未检测到测试执行")
            
            # 检查覆盖率
            coverage_summary = report_data.get('coverage_summary', {})
            if coverage_summary:
                print(f"\n📈 覆盖率:")
                for metric, value in coverage_summary.items():
                    print(f"  {metric}: {value}%")
            else:
                print("\n⚠️ 无覆盖率数据")
            
            # 检查HTML报告
            html_url = report_data.get('html_report_url')
            if html_url:
                print(f"\n🔗 HTML报告: {html_url}")
            
            return True
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

if __name__ == "__main__":
    quick_test()
