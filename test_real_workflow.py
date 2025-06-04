#!/usr/bin/env python3
"""
测试真实的工作流程：扫描实际项目代码并发送通知
"""

import requests
import json
import time

def test_real_project_workflow():
    """测试真实项目工作流程"""
    
    print("🔍 测试真实项目工作流程")
    print("=" * 60)
    
    # 模拟GitLab webhook数据
    payload = {
        "object_kind": "push",
        "ref": "refs/heads/main",
        "user_name": "kian",
        "project": {
            "name": "jacocotest",
            "http_url": "http://172.16.1.30/kian/jacocotest.git"
        },
        "commits": [{
            "id": "84d32a75d4832dc26f33678706bc8446da51cda0",
            "message": "Test real workflow - scan actual project code"
        }]
    }
    
    url = "http://localhost:8002/github/webhook-no-auth"
    
    print(f"📋 模拟GitLab推送:")
    print(f"  仓库: {payload['project']['http_url']}")
    print(f"  分支: {payload['ref']}")
    print(f"  提交: {payload['commits'][0]['id'][:8]}")
    print(f"  消息: {payload['commits'][0]['message']}")
    print()
    
    print(f"📤 发送webhook到JaCoCo API: {url}")
    print()
    
    try:
        print("⏳ 发送请求...")
        start_time = time.time()
        
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=600  # 10分钟超时
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ 请求耗时: {duration:.2f} 秒")
        print(f"📊 HTTP状态码: {response.status_code}")
        print()
        
        try:
            result = response.json()
            print(f"📄 API响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print()
            
            # 分析扫描结果
            analyze_scan_result(result)
            
        except json.JSONDecodeError:
            print(f"📄 响应文本: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时 - 扫描可能需要更长时间")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - 请确保JaCoCo API服务正在运行")
        print("💡 启动服务: python3 app.py")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def analyze_scan_result(result):
    """分析扫描结果"""
    
    print("📈 扫描结果分析:")
    print("-" * 40)
    
    status = result.get('status', 'unknown')
    print(f"📊 扫描状态: {status}")
    
    if status == 'completed':
        print("✅ 扫描成功完成")
        
        # 覆盖率信息
        coverage_percentage = result.get('coverage_percentage', 0)
        branch_coverage = result.get('branch_coverage', 0)
        lines_covered = result.get('lines_covered', 0)
        lines_total = result.get('lines_total', 0)
        
        print(f"📈 覆盖率数据:")
        print(f"  行覆盖率: {coverage_percentage}%")
        print(f"  分支覆盖率: {branch_coverage}%")
        print(f"  覆盖行数: {lines_covered}/{lines_total}")
        
        # 报告文件
        reports_available = result.get('reports_available', False)
        xml_report_path = result.get('xml_report_path')
        html_report_available = result.get('html_report_available', False)
        
        print(f"📄 报告文件:")
        print(f"  报告可用: {'✅' if reports_available else '❌'}")
        print(f"  XML报告: {'✅' if xml_report_path else '❌'}")
        print(f"  HTML报告: {'✅' if html_report_available else '❌'}")
        
    elif status == 'no_reports':
        print("⚠️ 扫描完成但没有生成报告")
        print("可能原因:")
        print("  - 项目没有测试代码")
        print("  - 项目没有主代码")
        print("  - JaCoCo配置问题")
        
        # 检查是否有默认覆盖率数据
        coverage_percentage = result.get('coverage_percentage', 'N/A')
        print(f"📈 默认覆盖率: {coverage_percentage}%")
        
    elif status == 'error':
        print("❌ 扫描失败")
        error_message = result.get('message', 'Unknown error')
        print(f"错误信息: {error_message}")
        
    elif status == 'accepted':
        print("⏳ 任务已排队（异步模式）")
        task_id = result.get('task_id', 'N/A')
        print(f"任务ID: {task_id}")
        
    # 通知状态
    print(f"\n📱 通知状态:")
    notification_sent = result.get('notification_sent', False)
    notification_error = result.get('notification_error')
    notification_skip_reason = result.get('notification_skip_reason')
    
    if notification_sent:
        print("✅ Lark通知已发送")
    elif notification_error:
        print(f"❌ Lark通知发送失败: {notification_error}")
    elif notification_skip_reason:
        print(f"⚠️ Lark通知被跳过: {notification_skip_reason}")
    else:
        print("❓ Lark通知状态未知")
    
    # 扫描方法
    scan_method = result.get('scan_method', 'unknown')
    print(f"\n🔧 扫描方法: {scan_method}")
    
    # 项目信息
    repo_url = result.get('repo_url')
    commit_id = result.get('commit_id')
    if repo_url and commit_id:
        print(f"\n📋 项目信息:")
        print(f"  仓库: {repo_url}")
        print(f"  提交: {commit_id[:8] if commit_id else 'N/A'}")

def check_service_status():
    """检查服务状态"""
    
    print("🔍 检查JaCoCo API服务状态")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            print("✅ JaCoCo API服务正常运行")
            return True
        else:
            print(f"⚠️ JaCoCo API服务状态异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ JaCoCo API服务未启动")
        print("💡 请先启动服务: python3 app.py")
        return False
    except Exception as e:
        print(f"❌ 检查服务状态失败: {e}")
        return False

def show_workflow_explanation():
    """显示工作流程说明"""
    
    print("📋 真实工作流程说明")
    print("=" * 60)
    print("1. 开发人员提交代码到GitLab")
    print("2. GitLab触发webhook到JaCoCo API")
    print("3. JaCoCo API克隆最新代码")
    print("4. 扫描实际项目代码（不创建示例代码）")
    print("5. 生成覆盖率报告（如果有测试）")
    print("6. 发送报告到Lark（无论覆盖率是否为0%）")
    print()
    print("📌 重要说明:")
    print("- 系统会扫描实际项目代码，不会创建示例代码")
    print("- 即使项目没有测试，也会发送0%覆盖率通知")
    print("- 通知包含项目信息、提交信息和覆盖率数据")
    print()

if __name__ == "__main__":
    show_workflow_explanation()
    
    # 检查服务状态
    if check_service_status():
        print()
        test_real_project_workflow()
    else:
        print("\n💡 请先启动JaCoCo API服务，然后重新运行此测试")
        print("   启动命令: python3 app.py")
