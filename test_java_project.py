#!/usr/bin/env python3
"""
测试Java项目的覆盖率扫描
专门测试backend-lotto-game项目
"""

import requests
import json
import time

def test_java_project():
    """测试Java项目扫描"""
    print("🔍 测试Java项目覆盖率扫描")
    print("=" * 60)
    
    # 检查服务状态
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code != 200:
            print("❌ JaCoCo API服务未运行")
            return False
    except Exception as e:
        print("❌ 无法连接到JaCoCo API服务")
        return False
    
    print("✅ 服务连接正常")
    
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
                "id": "main",  # 使用main分支的最新提交
                "message": "Test Java project coverage"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    print(f"\n📤 测试Java项目: {webhook_data['project']['name']}")
    print(f"仓库: {webhook_data['project']['http_url']}")
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8002/github/webhook-no-auth",
            json=webhook_data,
            timeout=600  # 增加超时时间，Java项目可能需要更长时间
        )
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ 处理时间: {duration:.1f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook处理成功")
            
            # 详细分析扫描结果
            scan_result = result.get('scan_result', {})
            report_data = result.get('report_data', {})
            
            print(f"\n📊 详细扫描分析:")
            print(f"  状态: {scan_result.get('status', 'unknown')}")
            print(f"  方法: {scan_result.get('scan_method', 'unknown')}")
            print(f"  返回码: {scan_result.get('return_code', 'N/A')}")
            
            # 检查Maven输出
            maven_output = scan_result.get('maven_output', '')
            if maven_output:
                print(f"\n📋 Maven执行分析:")
                if "BUILD SUCCESS" in maven_output:
                    print("✅ Maven构建成功")
                elif "BUILD FAILURE" in maven_output:
                    print("❌ Maven构建失败")
                    # 查找具体错误
                    lines = maven_output.split('\n')
                    for i, line in enumerate(lines):
                        if "ERROR" in line or "FAILURE" in line:
                            print(f"  错误: {line.strip()}")
                
                # 检查测试执行
                if "Tests run:" in maven_output:
                    print("✅ 检测到测试执行")
                    # 提取测试结果
                    for line in maven_output.split('\n'):
                        if "Tests run:" in line:
                            print(f"  测试结果: {line.strip()}")
                else:
                    print("⚠️ 未检测到测试执行")
                
                # 检查JaCoCo插件执行
                if "jacoco:report" in maven_output:
                    print("✅ JaCoCo报告插件已执行")
                else:
                    print("⚠️ JaCoCo报告插件未执行")
            
            # 检查项目结构
            if "主代码=True" in str(result):
                print("✅ 检测到Java主代码")
            elif "主代码=False" in str(result):
                print("⚠️ 未检测到Java主代码")
            
            if "测试代码=True" in str(result):
                print("✅ 检测到Java测试代码")
            elif "测试代码=False" in str(result):
                print("⚠️ 未检测到Java测试代码")
            
            # 检查覆盖率数据
            coverage_summary = report_data.get('coverage_summary', {})
            if coverage_summary:
                print(f"\n📈 覆盖率详情:")
                for metric, value in coverage_summary.items():
                    print(f"  {metric}: {value}%")
                
                # 分析为什么是0%
                if all(v == 0 for v in coverage_summary.values()):
                    print("\n🔍 0%覆盖率原因分析:")
                    print("  可能原因:")
                    print("  1. 测试未运行或失败")
                    print("  2. JaCoCo代理未正确附加")
                    print("  3. 测试代码未覆盖主代码")
                    print("  4. JaCoCo报告生成失败")
            
            # 检查报告文件
            if report_data.get('reports_available'):
                print("✅ JaCoCo报告文件已生成")
                xml_path = report_data.get('xml_report_path')
                if xml_path:
                    print(f"  XML报告: {xml_path}")
            else:
                print("❌ 未生成JaCoCo报告文件")
            
            # 检查HTML报告
            html_url = report_data.get('html_report_url')
            if html_url:
                print(f"✅ HTML报告: {html_url}")
            else:
                print("❌ 未生成HTML报告")
            
            return True
            
        else:
            print(f"❌ Webhook处理失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def analyze_zero_coverage():
    """分析0%覆盖率的常见原因"""
    print("\n🔍 Java项目0%覆盖率常见原因分析")
    print("=" * 60)
    
    print("1. **测试执行问题**:")
    print("   - 测试类命名不符合Maven规范（应以Test结尾或Test开头）")
    print("   - 测试方法没有@Test注解")
    print("   - 测试编译失败")
    print("   - 测试运行时异常")
    
    print("\n2. **JaCoCo配置问题**:")
    print("   - JaCoCo代理未正确附加到测试进程")
    print("   - JaCoCo插件配置错误")
    print("   - 测试和主代码的包路径不匹配")
    
    print("\n3. **项目结构问题**:")
    print("   - 主代码不在src/main/java目录")
    print("   - 测试代码不在src/test/java目录")
    print("   - 包结构不正确")
    
    print("\n4. **Maven配置问题**:")
    print("   - Surefire插件配置问题")
    print("   - 依赖冲突")
    print("   - Java版本不兼容")

def suggest_solutions():
    """建议解决方案"""
    print("\n💡 解决方案建议")
    print("=" * 60)
    
    print("1. **检查项目结构**:")
    print("   - 确保主代码在src/main/java")
    print("   - 确保测试代码在src/test/java")
    print("   - 检查包名是否正确")
    
    print("\n2. **检查测试代码**:")
    print("   - 测试类名以Test结尾（如UserServiceTest）")
    print("   - 测试方法有@Test注解")
    print("   - 测试实际调用了主代码")
    
    print("\n3. **增强JaCoCo配置**:")
    print("   - 确保JaCoCo代理正确配置")
    print("   - 检查包含/排除规则")
    print("   - 验证报告生成路径")
    
    print("\n4. **调试步骤**:")
    print("   - 本地运行: mvn clean test jacoco:report")
    print("   - 检查target/site/jacoco/目录")
    print("   - 查看详细的Maven日志")

def main():
    """主函数"""
    # 测试Java项目
    success = test_java_project()
    
    # 分析和建议
    analyze_zero_coverage()
    suggest_solutions()
    
    if success:
        print("\n🎯 下一步:")
        print("1. 查看上面的详细分析结果")
        print("2. 检查Maven输出中的错误信息")
        print("3. 验证项目的测试代码是否正确")
        print("4. 如需要，我可以帮您优化JaCoCo配置")
    else:
        print("\n❌ 测试失败，请检查服务状态")

if __name__ == "__main__":
    main()
