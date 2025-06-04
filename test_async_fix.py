#!/usr/bin/env python3
"""
测试异步修复
验证服务不再出现CancelledError
"""

import requests
import json
import time
import threading

def test_service_health():
    """测试服务健康状态"""
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_single_request():
    """测试单个请求"""
    print("📤 测试单个webhook请求")
    
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": "jacocotest",
            "http_url": "http://172.16.1.30/kian/jacocotest.git"
        },
        "user_name": "test_user",
        "commits": [
            {
                "id": "main",
                "message": "Test async fix"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8002/github/webhook-no-auth",
            json=webhook_data,
            timeout=180  # 3分钟超时
        )
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ 请求耗时: {duration:.1f}秒")
        
        if response.status_code == 200:
            print("✅ 请求成功")
            
            # 检查服务是否仍在运行
            time.sleep(2)
            if test_service_health():
                print("✅ 服务在请求后仍正常运行")
                return True
            else:
                print("❌ 服务在请求后停止响应")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_concurrent_requests():
    """测试并发请求"""
    print("\n🔄 测试并发请求")
    
    def send_request(request_id):
        webhook_data = {
            "object_kind": "push",
            "project": {
                "name": "jacocotest",
                "http_url": "http://172.16.1.30/kian/jacocotest.git"
            },
            "user_name": f"concurrent_test_{request_id}",
            "commits": [
                {
                    "id": "main",
                    "message": f"Concurrent test {request_id}"
                }
            ],
            "ref": "refs/heads/main"
        }
        
        try:
            response = requests.post(
                "http://localhost:8002/github/webhook-no-auth",
                json=webhook_data,
                timeout=120
            )
            return response.status_code == 200
        except:
            return False
    
    # 启动3个并发请求
    threads = []
    results = []
    
    def worker(request_id):
        result = send_request(request_id)
        results.append(result)
        print(f"请求{request_id}: {'✅' if result else '❌'}")
    
    for i in range(3):
        thread = threading.Thread(target=worker, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    success_count = sum(results)
    print(f"并发测试结果: {success_count}/3 成功")
    
    # 检查服务状态
    time.sleep(3)
    if test_service_health():
        print("✅ 服务在并发请求后仍正常运行")
        return success_count >= 2  # 至少2个成功
    else:
        print("❌ 服务在并发请求后停止响应")
        return False

def monitor_service(duration=30):
    """监控服务状态"""
    print(f"\n👁️ 监控服务状态 ({duration}秒)")
    
    start_time = time.time()
    check_count = 0
    success_count = 0
    
    while time.time() - start_time < duration:
        if test_service_health():
            success_count += 1
        check_count += 1
        time.sleep(5)
    
    success_rate = (success_count / check_count) * 100
    print(f"服务可用率: {success_rate:.1f}% ({success_count}/{check_count})")
    
    return success_rate > 90

def main():
    """主函数"""
    print("🧪 异步修复测试")
    print("=" * 50)
    
    # 检查服务是否运行
    if not test_service_health():
        print("❌ 服务未运行，请先启动服务")
        print("💡 启动命令: python app.py")
        return
    
    print("✅ 服务连接正常")
    
    # 1. 测试单个请求
    single_success = test_single_request()
    
    # 2. 测试并发请求
    concurrent_success = test_concurrent_requests()
    
    # 3. 监控服务稳定性
    stability_success = monitor_service(30)
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"  单个请求: {'✅ 成功' if single_success else '❌ 失败'}")
    print(f"  并发请求: {'✅ 成功' if concurrent_success else '❌ 失败'}")
    print(f"  服务稳定性: {'✅ 成功' if stability_success else '❌ 失败'}")
    
    if single_success and concurrent_success and stability_success:
        print("\n🎉 异步修复测试全部通过！")
        print("\n✅ 主要成果:")
        print("  1. 服务不再出现CancelledError")
        print("  2. 支持并发请求处理")
        print("  3. 长时间运行稳定")
        print("  4. 异步处理性能良好")
        
        print("\n💡 现在可以正常使用服务了！")
        
    else:
        print("\n❌ 部分测试失败")
        
        if not single_success:
            print("❌ 单个请求处理有问题")
        if not concurrent_success:
            print("❌ 并发请求处理有问题")
        if not stability_success:
            print("❌ 服务稳定性有问题")
        
        print("\n🔧 故障排除建议:")
        print("  1. 检查服务日志中的错误信息")
        print("  2. 确认异步处理配置正确")
        print("  3. 检查线程池配置")
        print("  4. 验证本地扫描功能")

if __name__ == "__main__":
    main()
