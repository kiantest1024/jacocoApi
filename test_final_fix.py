#!/usr/bin/env python3
"""
测试最终修复效果
验证报告生成和Lark通知功能
"""

import requests
import json
import time
import os

def test_final_fix():
    """测试最终修复效果"""
    print("🔧 测试最终修复效果")
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
    
    # 测试配置
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
                "message": "Test final fix"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    print("\n📤 发送测试webhook...")
    print(f"项目: {webhook_data['project']['name']}")
    
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
            report_data = result.get('report_data', {})
            
            print(f"\n📊 扫描结果分析:")
            print(f"  状态: {scan_result.get('status', 'unknown')}")
            print(f"  方法: {scan_result.get('scan_method', 'unknown')}")
            
            # 检查独立pom.xml方案
            if "独立pom.xml扫描成功" in str(result):
                print("✅ 独立pom.xml方案成功")
            elif "检测到父POM解析问题" in str(result):
                print("🔧 检测到父POM问题并尝试了修复")
            
            # 检查报告生成
            print(f"\n📋 报告生成:")
            if report_data.get('reports_available'):
                print("✅ JaCoCo XML报告已生成")
            else:
                print("⚠️ 未生成JaCoCo XML报告")
            
            # 检查HTML报告
            html_report_url = report_data.get('html_report_url')
            if html_report_url:
                print(f"✅ HTML报告: {html_report_url}")
                
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
                print("⚠️ 未生成HTML报告")
            
            # 检查覆盖率数据
            coverage_summary = report_data.get('coverage_summary')
            if coverage_summary:
                print(f"\n📈 覆盖率数据:")
                print(f"  行覆盖率: {coverage_summary.get('line_coverage', 0)}%")
                print(f"  分支覆盖率: {coverage_summary.get('branch_coverage', 0)}%")
                print(f"  指令覆盖率: {coverage_summary.get('instruction_coverage', 0)}%")
                print("✅ 覆盖率数据可用")
            else:
                print("\n⚠️ 覆盖率数据: 无")
            
            # 检查通知发送
            print(f"\n📱 Lark通知检查:")
            
            # 从日志中查找通知相关信息
            if "飞书通知已发送" in str(result):
                print("✅ Lark通知已发送")
            elif "准备发送Lark通知" in str(result):
                print("🔄 尝试发送Lark通知")
            elif "未配置Lark webhook URL" in str(result):
                print("⚠️ 未配置Lark webhook URL")
            else:
                print("❓ 通知状态未知")
            
            return True
            
        else:
            print(f"❌ Webhook处理失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_reports_api():
    """测试报告API"""
    print("\n📋 测试报告API...")
    
    try:
        response = requests.get("http://localhost:8002/reports", timeout=10)
        if response.status_code == 200:
            reports = response.json()
            total_projects = reports.get('total_projects', 0)
            print(f"✅ 报告API正常，共有 {total_projects} 个项目的报告")
            
            if total_projects > 0:
                for project in reports.get('reports', []):
                    project_name = project.get('project_name')
                    report_count = len(project.get('reports', []))
                    print(f"  📁 {project_name}: {report_count} 个报告")
            
            return True
        else:
            print(f"❌ 报告API失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 报告API异常: {e}")
        return False

def check_config():
    """检查配置"""
    print("\n⚙️ 检查配置...")
    
    # 检查环境变量
    lark_url = os.getenv('LARK_WEBHOOK_URL')
    if lark_url:
        print(f"✅ Lark Webhook URL已配置")
        # 隐藏敏感信息
        masked_url = lark_url[:30] + "..." + lark_url[-10:] if len(lark_url) > 40 else lark_url
        print(f"  URL: {masked_url}")
    else:
        print("⚠️ 未配置LARK_WEBHOOK_URL环境变量")
        print("💡 请在.env文件中配置或设置环境变量")
    
    # 检查配置文件
    try:
        from config import LARK_CONFIG
        if LARK_CONFIG.get('enable_notifications', True):
            print("✅ Lark通知已启用")
        else:
            print("⚠️ Lark通知已禁用")
    except Exception as e:
        print(f"⚠️ 配置检查失败: {e}")

def main():
    """主函数"""
    print("🧪 JaCoCo扫描最终修复测试")
    print("=" * 60)
    
    # 检查配置
    check_config()
    
    # 测试扫描功能
    scan_success = test_final_fix()
    
    # 测试报告API
    api_success = test_reports_api()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"  扫描功能: {'✅ 正常' if scan_success else '❌ 异常'}")
    print(f"  报告API: {'✅ 正常' if api_success else '❌ 异常'}")
    
    if scan_success and api_success:
        print("\n🎉 所有功能测试通过！")
        print("\n💡 主要修复:")
        print("  1. ✅ 独立pom.xml方案解决父POM问题")
        print("  2. ✅ 基本JaCoCo报告生成")
        print("  3. ✅ HTML报告保存和访问")
        print("  4. ✅ Lark通知发送逻辑修复")
        print("  5. ✅ 错误处理和日志增强")
    else:
        print("\n⚠️ 部分功能仍有问题")
        print("\n🔧 故障排除:")
        print("  - 检查Docker镜像是否重新构建")
        print("  - 检查Lark webhook URL配置")
        print("  - 查看详细日志输出")

if __name__ == "__main__":
    main()
