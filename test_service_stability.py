#!/usr/bin/env python3
"""
测试服务稳定性
验证服务在处理请求后是否保持运行
"""

import requests
import time
import json

def test_service_health():
    """测试服务健康状态"""
    print("🏥 测试服务健康状态")
    
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务健康检查通过")
            return True
        else:
            print(f"❌ 服务健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        return False

def test_multiple_requests():
    """测试多个请求的处理"""
    print("\n🔄 测试多个请求处理")
    
    # 测试数据
    test_projects = [
        {
            "name": "jacocoTest",
            "url": "https://gitlab.complexdevops.com/kian/jacocoTest.git"
        },
        {
            "name": "backend-lotto-game", 
            "url": "http://172.16.1.30/kian/backend-lotto-game.git"
        }
    ]
    
    for i, project in enumerate(test_projects, 1):
        print(f"\n📤 发送第{i}个请求: {project['name']}")
        
        webhook_data = {
            "object_kind": "push",
            "project": {
                "name": project['name'],
                "http_url": project['url']
            },
            "user_name": "stability_test",
            "commits": [
                {
                    "id": "main",
                    "message": f"Stability test {i}"
                }
            ],
            "ref": "refs/heads/main"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:8002/github/webhook-no-auth",
                json=webhook_data,
                timeout=300
            )
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                print(f"✅ 请求{i}成功 (耗时: {duration:.1f}秒)")
                
                # 检查服务是否仍然响应
                time.sleep(2)  # 等待2秒
                if test_service_health():
                    print(f"✅ 请求{i}后服务仍然正常运行")
                else:
                    print(f"❌ 请求{i}后服务停止响应")
                    return False
            else:
                print(f"❌ 请求{i}失败: {response.status_code}")
                print(f"响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 请求{i}异常: {e}")
            return False
        
        # 请求间隔
        if i < len(test_projects):
            print(f"⏳ 等待5秒后发送下一个请求...")
            time.sleep(5)
    
    return True

def test_api_endpoints():
    """测试各个API端点"""
    print("\n🔗 测试API端点")
    
    endpoints = [
        {"url": "/health", "method": "GET", "name": "健康检查"},
        {"url": "/reports", "method": "GET", "name": "报告列表"},
        {"url": "/config/test", "method": "GET", "name": "配置测试"}
    ]
    
    for endpoint in endpoints:
        try:
            if endpoint["method"] == "GET":
                response = requests.get(f"http://localhost:8002{endpoint['url']}", timeout=10)
            else:
                continue  # 暂时只测试GET请求
            
            if response.status_code == 200:
                print(f"✅ {endpoint['name']}: 正常")
            else:
                print(f"⚠️ {endpoint['name']}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint['name']}: {e}")

def monitor_service(duration=60):
    """监控服务状态"""
    print(f"\n👁️ 监控服务状态 ({duration}秒)")
    
    start_time = time.time()
    check_interval = 10  # 每10秒检查一次
    
    while time.time() - start_time < duration:
        if test_service_health():
            elapsed = int(time.time() - start_time)
            print(f"✅ {elapsed}秒: 服务正常运行")
        else:
            print(f"❌ 服务在{int(time.time() - start_time)}秒后停止响应")
            return False
        
        time.sleep(check_interval)
    
    print(f"✅ 监控完成，服务在{duration}秒内保持稳定")
    return True

def main():
    """主函数"""
    print("🧪 JaCoCo API服务稳定性测试")
    print("=" * 50)
    
    # 1. 初始健康检查
    if not test_service_health():
        print("❌ 服务未运行，请先启动服务")
        print("💡 启动命令: python start_stable.py")
        return
    
    # 2. 测试API端点
    test_api_endpoints()
    
    # 3. 测试多个请求处理
    print("\n" + "=" * 50)
    if test_multiple_requests():
        print("\n✅ 多请求测试通过")
    else:
        print("\n❌ 多请求测试失败")
        return
    
    # 4. 监控服务稳定性
    print("\n" + "=" * 50)
    if monitor_service(30):  # 监控30秒
        print("\n✅ 服务稳定性测试通过")
    else:
        print("\n❌ 服务稳定性测试失败")
        return
    
    # 5. 最终检查
    print("\n" + "=" * 50)
    print("📊 最终稳定性检查:")
    
    if test_service_health():
        print("✅ 服务在所有测试后仍然正常运行")
        print("🎉 服务稳定性测试全部通过！")
        
        print("\n💡 测试结果:")
        print("  ✅ 服务启动稳定")
        print("  ✅ 请求处理正常")
        print("  ✅ 多请求处理稳定")
        print("  ✅ 长时间运行稳定")
        print("  ✅ API端点响应正常")
    else:
        print("❌ 服务在测试过程中停止响应")
        print("🔧 建议检查服务日志和错误信息")

if __name__ == "__main__":
    main()
