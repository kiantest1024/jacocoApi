#!/usr/bin/env python3
"""测试调试版本的扫描功能"""

import requests
import json
import time

def test_debug_webhook():
    """测试调试版本的 webhook"""
    
    # 调试版本的 URL
    debug_url = "http://localhost:8003/github/webhook-no-auth"
    
    # 测试载荷
    payload = {
        "object_kind": "push",
        "project": {
            "name": "jacocotest",
            "http_url": "http://172.16.1.30/kian/jacocotest.git"
        },
        "commits": [{"id": "main"}],
        "ref": "refs/heads/main",
        "user_name": "kian"
    }
    
    print("🔍 测试调试版本扫描...")
    print(f"📡 目标URL: {debug_url}")
    print(f"📋 载荷: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        # 发送请求
        print("\n🚀 发送扫描请求...")
        response = requests.post(
            debug_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功")
            print(f"📋 响应数据:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 检查调试信息
            if "debug_info" in result:
                debug_info = result["debug_info"]
                print(f"\n🔍 调试信息:")
                print(f"  扫描方法: {debug_info.get('scan_method', 'unknown')}")
                
                if "scan_analysis" in debug_info:
                    analysis = debug_info["scan_analysis"]
                    print(f"  测试运行: {analysis.get('tests_run', 0)}")
                    print(f"  测试失败: {analysis.get('tests_failed', 0)}")
                    print(f"  编译错误: {len(analysis.get('compilation_errors', []))}")
            
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"📋 错误响应: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保调试服务正在运行")
        return False
    except Exception as e:
        print(f"💥 请求异常: {e}")
        return False

def test_debug_logs():
    """测试调试日志接口"""
    
    debug_logs_url = "http://localhost:8003/debug/logs"
    
    print(f"\n🔍 测试调试日志接口...")
    print(f"📡 目标URL: {debug_logs_url}")
    
    try:
        response = requests.get(debug_logs_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 调试日志获取成功")
            print(f"📊 日志状态: {result.get('status')}")
            print(f"📋 日志行数: {result.get('total_lines', 0)}")
            print(f"💬 消息: {result.get('message')}")
            
            # 显示最后几行日志
            logs = result.get('logs', [])
            if logs:
                print(f"\n📝 最近的日志 (显示最后5行):")
                for log_line in logs[-5:]:
                    print(f"  {log_line.strip()}")
            
            return True
        else:
            print(f"❌ 获取日志失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 获取日志异常: {e}")
        return False

def test_health_check():
    """测试健康检查"""
    
    health_url = "http://localhost:8003/health"
    
    print(f"\n🔍 测试健康检查...")
    print(f"📡 目标URL: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 健康检查成功")
            print(f"📊 状态: {result.get('status')}")
            print(f"🔍 调试模式: {result.get('debug_mode')}")
            print(f"📋 版本: {result.get('version')}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 健康检查异常: {e}")
        return False

def main():
    """主测试函数"""
    
    print("🧪 JaCoCo API 调试版本功能测试")
    print("=" * 50)
    
    # 测试列表
    tests = [
        ("健康检查", test_health_check),
        ("调试日志接口", test_debug_logs),
        ("调试扫描功能", test_debug_webhook),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 执行测试: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
                
        except Exception as e:
            print(f"💥 {test_name} 测试异常: {e}")
            results.append((test_name, False))
        
        # 测试间隔
        time.sleep(1)
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！调试版本工作正常。")
    else:
        print("⚠️  部分测试失败，请检查调试服务状态。")
    
    print("\n💡 提示:")
    print("  - 确保调试服务正在运行: python app_debug.py")
    print("  - 检查端口 8003 是否可访问")
    print("  - 查看调试日志: http://localhost:8003/debug/logs")

if __name__ == "__main__":
    main()
