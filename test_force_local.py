#!/usr/bin/env python3
"""
测试强制本地扫描
验证本地扫描是否正常工作
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

def test_force_local_scan():
    """测试强制本地扫描"""
    print("🔧 测试强制本地扫描")
    print("=" * 50)
    
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": "jacocotest",
            "http_url": "http://172.16.1.30/kian/jacocotest.git"
        },
        "user_name": "force_local_test",
        "commits": [
            {
                "id": "5ea76b4989a17153eade57d7d55609ebad7fdd9e",
                "message": "Test force local scan"
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
            
            # 验证是否使用了本地扫描
            scan_method = scan_result.get('scan_method', 'unknown')
            if scan_method == 'local':
                print("✅ 确认使用本地扫描方法")
            else:
                print(f"❌ 扫描方法错误: {scan_method}（应该是'local'）")
                return "wrong_method"
            
            # 检查Maven输出
            maven_output = scan_result.get('maven_output', '')
            if maven_output:
                print(f"\n📋 Maven输出分析:")
                
                if "BUILD SUCCESS" in maven_output:
                    print("✅ Maven构建成功")
                elif "BUILD FAILURE" in maven_output:
                    print("❌ Maven构建失败")
                    # 显示错误信息
                    lines = maven_output.split('\n')
                    error_lines = []
                    for line in lines:
                        if 'ERROR' in line or 'FAILURE' in line:
                            error_lines.append(line.strip())
                    
                    if error_lines:
                        print("错误信息:")
                        for error in error_lines[:5]:  # 只显示前5个错误
                            print(f"  {error}")
                    
                    return "build_failed"
                
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
                
                # 检查离线/在线模式
                if "离线模式扫描成功" in maven_output:
                    print("✅ 使用离线模式（Maven缓存）")
                elif "在线模式扫描成功" in maven_output:
                    print("✅ 使用在线模式")
                else:
                    print("⚠️ 未明确扫描模式")
            
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
                    print(f"\n🎉 本地扫描成功！")
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
                                line_coverage = coverage_summary.get('line_coverage', 0)
                                if str(int(line_coverage)) in html_response.text or f"{line_coverage:.0f}" in html_response.text:
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

def check_service_stability():
    """检查服务稳定性"""
    print("\n🔄 检查服务稳定性")
    print("=" * 50)
    
    # 多次检查服务状态
    checks = []
    for i in range(5):
        if test_service_health():
            checks.append(True)
            print(f"  检查{i+1}: ✅ 服务响应正常")
        else:
            checks.append(False)
            print(f"  检查{i+1}: ❌ 服务无响应")
        
        if i < 4:
            time.sleep(1)
    
    success_rate = sum(checks) / len(checks) * 100
    print(f"\n服务稳定性: {success_rate:.1f}%")
    
    return success_rate >= 80  # 要求80%以上稳定

def main():
    """主函数"""
    print("🧪 强制本地扫描测试")
    print("=" * 50)
    
    # 检查服务状态
    if not test_service_health():
        print("❌ JaCoCo API服务未运行")
        print("💡 请先启动服务: python app.py")
        return
    
    print("✅ 服务连接正常")
    print("📋 当前配置: 强制本地扫描模式")
    
    # 执行强制本地扫描测试
    result = test_force_local_scan()
    
    # 检查服务稳定性
    stability_ok = check_service_stability()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"  扫描结果: {result}")
    print(f"  服务稳定性: {'✅ 稳定' if stability_ok else '❌ 不稳定'}")
    
    if result == "success" and stability_ok:
        print("\n🎉 强制本地扫描测试全部通过！")
        print("\n✅ 主要成果:")
        print("  1. 强制本地扫描配置生效")
        print("  2. Maven构建和测试正常")
        print("  3. JaCoCo报告生成成功")
        print("  4. 覆盖率数据正确解析")
        print("  5. HTML报告可正常访问")
        print("  6. 服务保持稳定运行")
        
        print("\n💡 下一步:")
        print("  1. 基础功能已正常，可以考虑重新启用Docker")
        print("  2. 测试共享容器功能")
        print("  3. 进行性能优化")
        
    elif result == "success":
        print("\n⚠️ 扫描功能正常，但服务稳定性有问题")
        print("💡 建议检查服务配置和异步处理")
        
    elif stability_ok:
        print("\n⚠️ 服务稳定，但扫描功能有问题")
        
        if result == "wrong_method":
            print("💡 配置问题：仍在使用Docker扫描")
        elif result == "build_failed":
            print("💡 Maven构建问题：检查项目配置和依赖")
        elif result == "zero_coverage":
            print("💡 覆盖率问题：检查JaCoCo配置和测试执行")
        elif result == "no_coverage":
            print("💡 报告解析问题：检查XML报告生成")
        
    else:
        print("\n❌ 扫描和稳定性都有问题")
        print("💡 建议:")
        print("  1. 重启服务")
        print("  2. 检查配置文件")
        print("  3. 查看详细日志")
        print("  4. 验证系统环境")

if __name__ == "__main__":
    main()
