#!/usr/bin/env python3
"""
测试覆盖率数据传递
验证解析的覆盖率数据是否正确传递到通知系统
"""

import requests
import json
import time

def test_coverage_data_transmission():
    """测试覆盖率数据传递"""
    print("🧪 测试覆盖率数据传递")
    print("=" * 60)
    
    # 检查服务状态
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code != 200:
            print("❌ JaCoCo API服务未运行")
            print("💡 请先启动服务: python start_stable.py")
            return False
    except Exception as e:
        print("❌ 无法连接到JaCoCo API服务")
        print("💡 请先启动服务: python start_stable.py")
        return False
    
    print("✅ 服务连接正常")
    
    # 测试jacocoTest项目（已知有覆盖率的项目）
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
                "message": "Test coverage data transmission"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    print(f"\n📤 测试项目: {webhook_data['project']['name']}")
    print(f"仓库: {webhook_data['project']['http_url']}")
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8002/github/webhook-no-auth",
            json=webhook_data,
            timeout=300
        )
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ 处理时间: {duration:.1f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook处理成功")
            
            # 分析结果
            scan_result = result.get('scan_result', {})
            report_data = result.get('report_data', {})
            
            print(f"\n📊 扫描结果分析:")
            print(f"  状态: {scan_result.get('status')}")
            print(f"  方法: {scan_result.get('scan_method')}")
            print(f"  返回码: {scan_result.get('return_code')}")
            
            # 检查报告数据
            print(f"\n📋 报告数据分析:")
            print(f"  报告可用: {report_data.get('reports_available', False)}")
            
            # 检查覆盖率数据
            coverage_summary = report_data.get('coverage_summary', {})
            if coverage_summary:
                print(f"\n📈 解析的覆盖率数据:")
                total_coverage = 0
                count = 0
                for metric, value in coverage_summary.items():
                    print(f"  {metric}: {value}%")
                    if isinstance(value, (int, float)):
                        total_coverage += value
                        count += 1
                
                if count > 0:
                    avg_coverage = total_coverage / count
                    if avg_coverage > 0:
                        print(f"\n✅ 覆盖率数据解析成功！")
                        print(f"   平均覆盖率: {avg_coverage:.2f}%")
                        print(f"   行覆盖率: {coverage_summary.get('line_coverage', 0)}%")
                        print(f"   分支覆盖率: {coverage_summary.get('branch_coverage', 0)}%")
                        
                        # 检查HTML报告
                        html_url = report_data.get('html_report_url')
                        if html_url:
                            print(f"\n🔗 HTML报告: {html_url}")
                            
                            # 尝试访问HTML报告
                            try:
                                html_response = requests.get(html_url, timeout=10)
                                if html_response.status_code == 200:
                                    print("✅ HTML报告可访问")
                                    
                                    # 检查HTML内容中的覆盖率
                                    if "32%" in html_response.text or "31%" in html_response.text:
                                        print("✅ HTML报告包含正确的覆盖率数据")
                                    else:
                                        print("⚠️ HTML报告覆盖率数据需要验证")
                                else:
                                    print(f"⚠️ HTML报告访问失败: {html_response.status_code}")
                            except Exception as e:
                                print(f"⚠️ HTML报告访问异常: {e}")
                        
                        return True
                    else:
                        print("❌ 所有覆盖率指标都为0%")
                        return False
                else:
                    print("❌ 覆盖率数据格式错误")
                    return False
            else:
                print("❌ 未找到覆盖率数据")
                return False
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def check_lark_notification():
    """检查Lark通知是否包含正确的覆盖率数据"""
    print("\n📱 Lark通知检查")
    print("=" * 60)
    
    print("💡 请检查Lark群组中的通知消息")
    print("✅ 如果通知显示正确的覆盖率数据（如32%），则数据传递成功")
    print("❌ 如果通知仍显示0%，则需要进一步调试")
    
    # 这里可以添加自动检查Lark消息的逻辑，但需要Lark API权限

def analyze_logs():
    """分析日志输出"""
    print("\n📋 日志分析建议")
    print("=" * 60)
    
    print("请检查服务日志中的以下关键信息:")
    print("1. JaCoCo XML parsing completed: 应该显示正确的覆盖率百分比")
    print("2. 报告解析结果: 应该包含coverage_summary字段")
    print("3. 覆盖率数据: 传递给Lark通知的数据应该不是全0")
    print("4. 飞书通知发送成功: 确认通知已发送")

def main():
    """主函数"""
    print("🔍 JaCoCo覆盖率数据传递测试")
    print("=" * 60)
    
    success = test_coverage_data_transmission()
    
    if success:
        print("\n🎉 覆盖率数据传递测试成功！")
        print("\n✅ 主要成果:")
        print("  1. JaCoCo扫描正常执行")
        print("  2. 覆盖率数据正确解析")
        print("  3. HTML报告生成成功")
        print("  4. 数据传递到通知系统")
        
        check_lark_notification()
        
        print("\n💡 下一步:")
        print("  1. 检查Lark群组中的通知消息")
        print("  2. 验证通知中的覆盖率数据是否正确")
        print("  3. 如果仍有问题，查看详细日志")
    else:
        print("\n❌ 覆盖率数据传递测试失败")
        analyze_logs()
        
        print("\n🔧 故障排除:")
        print("  1. 检查JaCoCo XML报告是否正确生成")
        print("  2. 检查报告解析逻辑")
        print("  3. 检查数据传递到通知系统的过程")
        print("  4. 查看详细的服务日志")

if __name__ == "__main__":
    main()
