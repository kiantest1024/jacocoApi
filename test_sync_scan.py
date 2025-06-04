#!/usr/bin/env python3
"""
测试同步扫描功能
"""

import requests
import json
import time

def test_sync_scan():
    """测试同步扫描"""
    
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
            "message": "Test commit"
        }]
    }
    
    url = "http://localhost:8002/github/webhook-no-auth"
    
    print("🧪 测试同步JaCoCo扫描")
    print("=" * 50)
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
            timeout=300  # 5分钟超时
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
            if status == 'completed':
                print("\n✅ 扫描成功完成！")
                
                # 显示覆盖率信息
                report_data = result.get('report_data', {})
                if 'coverage_summary' in report_data:
                    coverage = report_data['coverage_summary']
                    print(f"📈 行覆盖率: {coverage.get('line_coverage', 'N/A')}%")
                    print(f"🌿 分支覆盖率: {coverage.get('branch_coverage', 'N/A')}%")
                
            elif status == 'error':
                print(f"\n❌ 扫描失败: {result.get('message', 'Unknown error')}")
                error_details = result.get('error_details')
                if error_details:
                    print(f"🔍 错误详情: {error_details}")
                    
            elif status == 'accepted':
                print(f"\n⏳ 任务已排队: {result.get('task_id', 'N/A')}")
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
    print("🔍 检查服务状态...")
    if check_service():
        print()
        test_sync_scan()
    else:
        print("\n💡 请先启动服务:")
        print("   python3 app.py")
        print("   或")
        print("   ./start_complete.sh")
