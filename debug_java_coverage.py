#!/usr/bin/env python3
"""
调试Java项目覆盖率问题
"""

import requests
import json

def debug_java_coverage():
    """调试Java覆盖率"""
    print("🐛 调试Java项目覆盖率问题")
    print("=" * 60)
    
    # 发送webhook请求
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": "backend-lotto-game",
            "http_url": "http://172.16.1.30/kian/backend-lotto-game.git"
        },
        "user_name": "debug_user",
        "commits": [
            {
                "id": "main",
                "message": "Debug Java coverage"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    print("📤 发送调试请求...")
    
    try:
        response = requests.post(
            "http://localhost:8002/github/webhook-no-auth",
            json=webhook_data,
            timeout=600
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 详细分析结果
            scan_result = result.get('scan_result', {})
            report_data = result.get('report_data', {})
            
            print("✅ 请求成功，分析结果...")
            
            # 1. 基本信息
            print(f"\n📊 基本信息:")
            print(f"  状态: {scan_result.get('status')}")
            print(f"  扫描方法: {scan_result.get('scan_method')}")
            print(f"  返回码: {scan_result.get('return_code')}")
            
            # 2. Maven输出分析
            maven_output = scan_result.get('maven_output', '')
            print(f"\n📋 Maven输出分析:")
            
            if maven_output:
                # 检查构建状态
                if "BUILD SUCCESS" in maven_output:
                    print("✅ Maven构建成功")
                elif "BUILD FAILURE" in maven_output:
                    print("❌ Maven构建失败")
                else:
                    print("⚠️ 构建状态未知")
                
                # 检查编译
                if "Compiling" in maven_output:
                    print("✅ 检测到编译过程")
                    # 统计编译的文件数
                    compile_lines = [line for line in maven_output.split('\n') if 'Compiling' in line]
                    if compile_lines:
                        print(f"  编译信息: {compile_lines[0]}")
                
                # 检查测试执行
                if "Tests run:" in maven_output:
                    print("✅ 检测到测试执行")
                    test_lines = [line for line in maven_output.split('\n') if 'Tests run:' in line]
                    for line in test_lines:
                        print(f"  {line.strip()}")
                else:
                    print("⚠️ 未检测到测试执行")
                
                # 检查JaCoCo执行
                if "jacoco" in maven_output.lower():
                    print("✅ 检测到JaCoCo执行")
                    jacoco_lines = [line for line in maven_output.split('\n') if 'jacoco' in line.lower()]
                    for line in jacoco_lines[:3]:  # 显示前3行
                        print(f"  {line.strip()}")
                else:
                    print("⚠️ 未检测到JaCoCo执行")
                
                # 检查错误
                error_lines = [line for line in maven_output.split('\n') if 'ERROR' in line or 'FAILURE' in line]
                if error_lines:
                    print("❌ 发现错误:")
                    for line in error_lines[:3]:  # 显示前3个错误
                        print(f"  {line.strip()}")
            else:
                print("⚠️ 无Maven输出")
            
            # 3. 覆盖率数据分析
            print(f"\n📈 覆盖率数据分析:")
            coverage_summary = report_data.get('coverage_summary', {})
            
            if coverage_summary:
                print("✅ 找到覆盖率数据:")
                for metric, value in coverage_summary.items():
                    print(f"  {metric}: {value}%")
                
                # 分析为什么是0%
                if all(v == 0 for v in coverage_summary.values()):
                    print("\n🔍 0%覆盖率可能原因:")
                    print("  1. 测试未实际运行")
                    print("  2. 测试未覆盖主代码")
                    print("  3. JaCoCo代理未正确附加")
                    print("  4. 包路径不匹配")
            else:
                print("❌ 未找到覆盖率数据")
            
            # 4. 报告文件分析
            print(f"\n📄 报告文件分析:")
            if report_data.get('reports_available'):
                print("✅ JaCoCo报告已生成")
                xml_path = report_data.get('xml_report_path')
                if xml_path:
                    print(f"  XML报告: {xml_path}")
            else:
                print("❌ 未生成JaCoCo报告")
            
            # 5. HTML报告
            html_url = report_data.get('html_report_url')
            if html_url:
                print(f"✅ HTML报告: {html_url}")
                
                # 尝试访问HTML报告
                try:
                    html_response = requests.get(html_url, timeout=10)
                    if html_response.status_code == 200:
                        print("✅ HTML报告可访问")
                        # 检查报告内容
                        if "0%" in html_response.text:
                            print("⚠️ HTML报告显示0%覆盖率")
                        if "No source code" in html_response.text:
                            print("⚠️ HTML报告显示无源代码")
                    else:
                        print(f"⚠️ HTML报告访问失败: {html_response.status_code}")
                except Exception as e:
                    print(f"⚠️ HTML报告访问异常: {e}")
            else:
                print("❌ 未生成HTML报告")
            
            # 6. 项目结构信息
            print(f"\n📁 项目结构信息:")
            if "主代码=True" in str(result):
                print("✅ 检测到主代码")
            elif "主代码=False" in str(result):
                print("⚠️ 未检测到主代码")
            
            if "测试代码=True" in str(result):
                print("✅ 检测到测试代码")
            elif "测试代码=False" in str(result):
                print("⚠️ 未检测到测试代码")
            
            # 7. 建议
            print(f"\n💡 调试建议:")
            
            if scan_result.get('return_code') != 0:
                print("1. Maven执行失败，检查依赖和配置")
            
            if "Tests run:" not in maven_output:
                print("2. 测试未运行，检查测试代码和Surefire配置")
            
            if "jacoco" not in maven_output.lower():
                print("3. JaCoCo插件未执行，检查插件配置")
            
            if all(v == 0 for v in coverage_summary.values()) if coverage_summary else True:
                print("4. 覆盖率为0%，检查测试是否实际调用主代码")
            
            return True
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 调试异常: {e}")
        return False

if __name__ == "__main__":
    debug_java_coverage()
