#!/usr/bin/env python3
"""
测试纯本地扫描功能
"""

import requests
import json
import time

def test_local_scan():
    """测试本地扫描"""
    
    # 测试数据
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
            "message": "Test local scan"
        }]
    }
    
    url = "http://localhost:8002/github/webhook-no-auth"
    
    print("🧪 测试本地JaCoCo扫描（跳过Docker）")
    print("=" * 60)
    print(f"📋 发送webhook到: {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
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
        print(f"📊 状态码: {response.status_code}")
        
        try:
            result = response.json()
            print(f"📄 响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 分析结果
            status = result.get('status', 'unknown')
            scan_result = result.get('scan_result', {})
            scan_method = scan_result.get('scan_method', 'unknown')
            
            print(f"\n📈 扫描结果分析:")
            print(f"  状态: {status}")
            print(f"  扫描方式: {scan_method}")
            
            if status == 'completed':
                print("✅ 扫描成功完成！")
                
                # 显示覆盖率信息
                report_data = result.get('report_data', {})
                if 'coverage_percentage' in report_data:
                    print(f"  📈 行覆盖率: {report_data.get('coverage_percentage', 'N/A')}%")
                    print(f"  🌿 分支覆盖率: {report_data.get('branch_coverage', 'N/A')}%")
                    print(f"  📊 覆盖行数: {report_data.get('lines_covered', 'N/A')}/{report_data.get('lines_total', 'N/A')}")
                
                # 检查是否发送了通知
                if 'message' in result and '飞书通知已发送' in str(result):
                    print("  📱 飞书通知: 已发送")
                else:
                    print("  📱 飞书通知: 未发送或失败")
                    
            elif status == 'error':
                print(f"❌ 扫描失败: {result.get('message', 'Unknown error')}")
                error_details = result.get('error_details')
                if error_details:
                    print(f"🔍 错误详情: {error_details}")
                    
            elif status == 'accepted':
                print(f"⏳ 任务已排队: {result.get('task_id', 'N/A')}")
                print("💡 如果使用异步模式，请检查Celery Worker是否运行")
                
        except json.JSONDecodeError:
            print(f"📄 响应文本: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时 - 扫描可能需要更长时间")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - 请确保服务正在运行")
        print("💡 启动服务: python3 app.py")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def check_dependencies():
    """检查本地依赖"""
    import subprocess
    
    dependencies = [
        ("git", "git --version"),
        ("maven", "mvn --version"),
        ("java", "java -version")
    ]
    
    print("🔍 检查本地扫描依赖:")
    all_ok = True
    
    for name, cmd in dependencies:
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_info = result.stdout.split('\n')[0] if result.stdout else result.stderr.split('\n')[0]
                print(f"  ✅ {name}: {version_info}")
            else:
                print(f"  ❌ {name}: 不可用")
                all_ok = False
        except Exception as e:
            print(f"  ❌ {name}: 检查失败 - {e}")
            all_ok = False
    
    return all_ok

def check_service():
    """检查服务状态"""
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务正常运行")
            return True
        else:
            print(f"⚠️ 服务状态异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务未启动: {e}")
        return False

if __name__ == "__main__":
    print("🔍 检查环境...")
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 本地依赖不完整，请先安装:")
        print("Ubuntu: sudo apt install git maven openjdk-11-jdk")
        print("Windows: 安装Git、Maven、Java")
        exit(1)
    
    print()
    
    # 检查服务
    if check_service():
        print()
        test_local_scan()
    else:
        print("\n💡 请先启动服务:")
        print("   python3 app.py")
        print("\n📋 确保配置已修改为使用本地扫描:")
        print("   config.py 中 use_docker=False, force_local_scan=True")
