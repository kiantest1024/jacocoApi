#!/usr/bin/env python3
"""快速测试扫描功能，避免长时间等待"""

import requests
import json
import time
import threading

def test_with_timeout():
    """测试调试版本扫描，带超时控制"""
    
    url = "http://localhost:8003/github/webhook-no-auth"
    
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
    
    print("🧪 测试调试版本扫描 (3分钟超时)")
    print("=" * 40)
    print(f"📡 URL: {url}")
    print(f"📋 载荷: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    start_time = time.time()
    
    def progress_monitor():
        """进度监控"""
        while True:
            elapsed = time.time() - start_time
            print(f"⏱️  已运行: {elapsed:.1f}秒")
            
            if elapsed > 200:  # 超过3分钟多一点就警告
                print("⚠️  扫描时间较长，可能遇到问题")
            
            time.sleep(30)  # 每30秒报告一次
    
    # 启动进度监控
    monitor_thread = threading.Thread(target=progress_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    try:
        print("\n🚀 发送扫描请求...")
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=240  # 4分钟客户端超时
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️  总耗时: {duration:.1f}秒")
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功")
            
            # 显示关键信息
            if "status" in result:
                print(f"📋 状态: {result['status']}")
            
            if "debug_info" in result:
                debug_info = result["debug_info"]
                print(f"🔍 扫描方法: {debug_info.get('scan_method', 'unknown')}")
                
                if "scan_analysis" in debug_info:
                    analysis = debug_info["scan_analysis"]
                    print(f"📊 测试统计:")
                    print(f"   运行: {analysis.get('tests_run', 0)}")
                    print(f"   失败: {analysis.get('tests_failed', 0)}")
                    print(f"   错误: {analysis.get('tests_errors', 0)}")
            
            if "message" in result:
                print(f"💬 消息: {result['message']}")
            
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"📋 响应: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时 (4分钟)")
        print("💡 这表明服务器端处理时间过长")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败")
        print("💡 请确保调试服务正在运行: python app_debug.py")
        return False
    except Exception as e:
        print(f"💥 请求异常: {e}")
        return False

def check_debug_logs():
    """检查调试日志"""
    try:
        print("\n🔍 获取调试日志...")
        response = requests.get("http://localhost:8003/debug/logs", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            logs = result.get('logs', [])
            
            print(f"📋 日志状态: {result.get('status')}")
            print(f"📊 总行数: {result.get('total_lines', 0)}")
            
            if logs:
                print("\n📝 最新日志 (最后10行):")
                for log_line in logs[-10:]:
                    print(f"  {log_line.strip()}")
            
            return True
        else:
            print(f"❌ 获取日志失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"💥 获取日志异常: {e}")
        return False

def main():
    """主函数"""
    print("🧪 JaCoCo 调试版本快速测试")
    print("=" * 40)
    
    # 检查服务是否运行
    try:
        response = requests.get("http://localhost:8003/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 调试服务运行正常")
            print(f"📋 版本: {result.get('version')}")
            print(f"🔍 调试模式: {result.get('debug_mode')}")
        else:
            print("❌ 调试服务状态异常")
            return
    except:
        print("❌ 无法连接到调试服务")
        print("💡 请启动调试服务: python app_debug.py")
        return
    
    print("\n" + "=" * 40)
    
    # 运行测试
    success = test_with_timeout()
    
    # 获取日志
    check_debug_logs()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 测试完成！")
    else:
        print("⚠️  测试遇到问题，请查看日志")
    
    print("\n💡 提示:")
    print("- 调试版本现在使用3分钟超时")
    print("- 如果仍然超时，可能是项目本身的问题")
    print("- 可以尝试本地扫描或检查项目代码")

if __name__ == "__main__":
    main()
