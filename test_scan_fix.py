#!/usr/bin/env python3
"""
测试扫描修复效果
专门测试父POM解析问题的修复
"""

import requests
import json
import time

def test_problematic_project():
    """测试有问题的项目扫描"""
    print("🧪 测试父POM解析问题修复")
    print("=" * 60)
    
    # 检查服务状态
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code != 200:
            print("❌ JaCoCo API服务未运行")
            print("💡 请先启动服务: python app.py")
            return False
    except Exception as e:
        print("❌ 无法连接到JaCoCo API服务")
        print("💡 请先启动服务: python app.py")
        return False
    
    print("✅ 服务连接正常")
    
    # 测试有父POM问题的项目
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": "backend-base-api-auto-build",
            "http_url": "http://172.16.1.30/kian/backend-base-api-auto-build.git"
        },
        "user_name": "test_user",
        "commits": [
            {
                "id": "acac855db57b883c986a95c3df18b886aea01692",
                "message": "Test parent POM fix"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    print("\n📤 发送测试webhook...")
    print(f"项目: {webhook_data['project']['name']}")
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
            
            # 分析扫描结果
            scan_result = result.get('scan_result', {})
            status = scan_result.get('status', 'unknown')
            scan_method = scan_result.get('scan_method', 'unknown')
            
            print(f"\n📊 扫描结果:")
            print(f"  状态: {status}")
            print(f"  方法: {scan_method}")
            
            # 检查Docker扫描
            if scan_method == "docker":
                print("🐳 Docker扫描成功")
            elif scan_method == "local":
                print("💻 本地扫描成功")
                
                # 检查是否使用了独立pom.xml
                maven_output = scan_result.get('maven_output', '')
                if "独立pom.xml扫描成功" in str(result):
                    print("✅ 独立pom.xml方案成功")
                elif "Non-resolvable parent POM" in maven_output:
                    print("⚠️ 仍然存在父POM问题")
                    
                    # 检查是否尝试了回退方案
                    if "检测到父POM解析问题" in str(result):
                        print("🔧 系统检测到父POM问题并尝试了修复")
                    else:
                        print("❌ 系统未检测到父POM问题")
            
            # 检查覆盖率数据
            coverage_summary = scan_result.get('coverage_summary', {})
            if coverage_summary:
                print(f"\n📈 覆盖率数据:")
                print(f"  行覆盖率: {coverage_summary.get('line_coverage', 0)}%")
                print(f"  分支覆盖率: {coverage_summary.get('branch_coverage', 0)}%")
                print(f"  指令覆盖率: {coverage_summary.get('instruction_coverage', 0)}%")
            else:
                print("\n📈 覆盖率数据: 无")
            
            # 检查HTML报告
            html_report_url = result.get('report_data', {}).get('html_report_url')
            if html_report_url:
                print(f"\n🔗 HTML报告: {html_report_url}")
                
                # 测试HTML报告访问
                try:
                    report_response = requests.get(html_report_url, timeout=10)
                    if report_response.status_code == 200:
                        print("✅ HTML报告可访问")
                    else:
                        print(f"⚠️ HTML报告访问异常: {report_response.status_code}")
                except Exception as e:
                    print(f"⚠️ HTML报告访问失败: {e}")
            else:
                print("\n🔗 HTML报告: 无")
            
            # 检查通知发送
            notification_sent = scan_result.get('notification_sent')
            if notification_sent:
                print("\n📱 Lark通知: 已发送")
            else:
                print("\n📱 Lark通知: 未发送或失败")
            
            return True
            
        else:
            print(f"❌ Webhook处理失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def analyze_logs():
    """分析日志输出"""
    print("\n📋 日志分析建议:")
    print("=" * 60)
    
    print("1. 查看Docker扫描日志:")
    print("   - 检查是否有MaxPermSize错误")
    print("   - 检查Docker镜像是否正确构建")
    
    print("\n2. 查看本地扫描日志:")
    print("   - 检查是否检测到父POM问题")
    print("   - 检查是否尝试了独立pom.xml方案")
    print("   - 检查Maven输出中的具体错误")
    
    print("\n3. 查看回退方案日志:")
    print("   - 检查独立pom.xml是否创建成功")
    print("   - 检查独立扫描的返回码")
    print("   - 检查是否生成了JaCoCo报告")

def main():
    """主函数"""
    success = test_problematic_project()
    
    if success:
        print("\n🎉 测试完成！")
        print("\n💡 如果扫描仍然失败，请检查:")
        print("1. Docker镜像是否重新构建")
        print("2. 独立pom.xml方案是否正常工作")
        print("3. 项目是否真的有Java源代码")
    else:
        print("\n❌ 测试失败！")
        analyze_logs()
    
    print("\n🔧 故障排除:")
    print("- 重新构建Docker镜像: ./rebuild-docker.sh")
    print("- 查看详细日志: 检查控制台输出")
    print("- 诊断工具: python diagnose_scan_issues.py")

if __name__ == "__main__":
    main()
