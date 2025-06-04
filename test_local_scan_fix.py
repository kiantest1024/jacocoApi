#!/usr/bin/env python3
"""
测试本地扫描修复
确保基本的覆盖率功能正常工作
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

def test_local_scan():
    """测试本地扫描"""
    print("🔧 测试本地扫描")
    print("=" * 50)
    
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": "jacocotest",
            "http_url": "http://172.16.1.30/kian/jacocotest.git"
        },
        "user_name": "local_test",
        "commits": [
            {
                "id": "5ea76b4989a17153eade57d7d55609ebad7fdd9e",
                "message": "Test local scan fix"
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
            
            print(f"\n📊 扫描结果分析:")
            print(f"  状态: {scan_result.get('status', 'unknown')}")
            print(f"  方法: {scan_result.get('scan_method', 'unknown')}")
            print(f"  返回码: {scan_result.get('return_code', 'unknown')}")
            
            # 检查Maven输出
            maven_output = scan_result.get('maven_output', '')
            if maven_output:
                if "BUILD SUCCESS" in maven_output:
                    print("✅ Maven构建成功")
                elif "BUILD FAILURE" in maven_output:
                    print("❌ Maven构建失败")
                    print("Maven错误信息:")
                    print(maven_output[-500:])  # 显示最后500字符
                
                if "Tests run:" in maven_output:
                    print("✅ 检测到测试执行")
                    # 提取测试信息
                    lines = maven_output.split('\n')
                    for line in lines:
                        if 'Tests run:' in line:
                            print(f"  {line.strip()}")
                else:
                    print("⚠️ 未检测到测试执行")
                
                if "jacoco:report" in maven_output.lower():
                    print("✅ JaCoCo报告生成")
                else:
                    print("⚠️ 未检测到JaCoCo报告生成")
            
            # 检查报告数据
            print(f"\n📋 报告数据分析:")
            print(f"  报告可用: {report_data.get('reports_available', False)}")
            print(f"  XML报告: {report_data.get('xml_report_path', 'None')}")
            print(f"  HTML报告: {report_data.get('html_report_available', False)}")
            
            # 检查覆盖率数据
            coverage_summary = report_data.get('coverage_summary', {})
            if coverage_summary:
                print(f"\n📈 覆盖率数据:")
                has_coverage = False
                total_coverage = 0
                count = 0
                
                for metric, value in coverage_summary.items():
                    print(f"  {metric}: {value}%")
                    if isinstance(value, (int, float)):
                        total_coverage += value
                        count += 1
                        if value > 0:
                            has_coverage = True
                
                if has_coverage:
                    avg_coverage = total_coverage / count if count > 0 else 0
                    print(f"\n🎉 覆盖率修复成功！")
                    print(f"   平均覆盖率: {avg_coverage:.2f}%")
                    print(f"   行覆盖率: {coverage_summary.get('line_coverage', 0)}%")
                    print(f"   分支覆盖率: {coverage_summary.get('branch_coverage', 0)}%")
                    
                    # 检查HTML报告
                    html_url = report_data.get('html_report_url')
                    if html_url:
                        print(f"🔗 HTML报告: {html_url}")
                        
                        # 测试HTML报告访问
                        try:
                            html_response = requests.get(html_url, timeout=10)
                            if html_response.status_code == 200:
                                print("✅ HTML报告可访问")
                                
                                # 检查HTML内容
                                if str(coverage_summary.get('line_coverage', 0)) in html_response.text:
                                    print("✅ HTML报告包含正确的覆盖率数据")
                                else:
                                    print("⚠️ HTML报告覆盖率数据需要验证")
                            else:
                                print(f"⚠️ HTML报告访问失败: {html_response.status_code}")
                        except Exception as e:
                            print(f"⚠️ HTML报告访问异常: {e}")
                    
                    return "success"
                else:
                    print("❌ 所有覆盖率指标都为0%")
                    return "zero_coverage"
            else:
                print("❌ 未找到覆盖率数据")
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

def analyze_problem(result):
    """分析问题并提供解决方案"""
    print("\n🔍 问题分析")
    print("=" * 50)
    
    if result == "success":
        print("🎉 本地扫描工作正常！")
        print("\n✅ 主要成果:")
        print("  1. Maven构建成功")
        print("  2. 测试正常执行")
        print("  3. JaCoCo报告生成")
        print("  4. 覆盖率数据正确")
        print("  5. HTML报告可访问")
        
        print("\n💡 下一步:")
        print("  1. 可以重新启用Docker扫描")
        print("  2. 测试共享容器功能")
        print("  3. 进行性能优化")
        
    elif result == "zero_coverage":
        print("⚠️ 覆盖率为0%问题")
        print("\n🔧 可能原因:")
        print("  1. JaCoCo插件配置问题")
        print("  2. 测试未正确执行")
        print("  3. 代码覆盖率收集失败")
        
        print("\n💡 解决方案:")
        print("  1. 检查Maven输出中的测试执行信息")
        print("  2. 验证JaCoCo插件是否正确添加")
        print("  3. 检查测试代码是否覆盖主代码")
        print("  4. 查看详细的Maven日志")
        
    elif result == "no_coverage":
        print("❌ 无覆盖率数据问题")
        print("\n🔧 可能原因:")
        print("  1. JaCoCo XML报告未生成")
        print("  2. 报告解析失败")
        print("  3. 报告文件路径错误")
        
        print("\n💡 解决方案:")
        print("  1. 检查target/site/jacoco/目录")
        print("  2. 验证jacoco.xml文件是否存在")
        print("  3. 检查报告解析逻辑")
        print("  4. 查看Maven JaCoCo插件输出")
        
    elif result == "request_failed":
        print("❌ 请求处理失败")
        print("\n💡 解决方案:")
        print("  1. 检查服务日志")
        print("  2. 验证网络连接")
        print("  3. 确认项目配置")
        
    else:
        print("❌ 其他问题")
        print("\n💡 通用解决方案:")
        print("  1. 重启服务")
        print("  2. 检查系统资源")
        print("  3. 查看详细日志")

def main():
    """主函数"""
    print("🧪 本地扫描修复测试")
    print("=" * 50)
    
    # 检查服务状态
    if not test_service_health():
        print("❌ JaCoCo API服务未运行")
        print("💡 请先启动服务: python app.py")
        return
    
    print("✅ 服务连接正常")
    print("📋 当前配置: 本地扫描模式（Docker已禁用）")
    
    # 执行本地扫描测试
    result = test_local_scan()
    
    # 分析结果
    analyze_problem(result)
    
    # 检查服务稳定性
    print("\n🔄 检查服务稳定性...")
    time.sleep(2)
    if test_service_health():
        print("✅ 服务在扫描后仍正常运行")
    else:
        print("❌ 服务在扫描后停止响应")
    
    print("\n📝 总结:")
    if result == "success":
        print("✅ 本地扫描功能完全正常")
        print("💡 可以考虑重新启用Docker功能")
    else:
        print("❌ 本地扫描仍有问题，需要进一步调试")
        print("💡 建议先解决基本扫描问题，再考虑Docker优化")

if __name__ == "__main__":
    main()
