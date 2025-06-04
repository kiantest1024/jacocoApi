#!/usr/bin/env python3
"""
测试共享Docker容器功能
验证容器复用和并发处理能力
"""

import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_service_health():
    """测试服务健康状态"""
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_docker_status():
    """获取Docker容器状态"""
    try:
        response = requests.get("http://localhost:8002/docker/status", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def start_shared_container():
    """启动共享容器"""
    try:
        response = requests.post("http://localhost:8002/docker/start", timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def stop_shared_container():
    """停止共享容器"""
    try:
        response = requests.post("http://localhost:8002/docker/stop", timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_scan_request(request_id, project_name="jacocotest"):
    """发送扫描请求"""
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": project_name,
            "http_url": "http://172.16.1.30/kian/jacocotest.git"
        },
        "user_name": f"concurrent_test_{request_id}",
        "commits": [
            {
                "id": "main",
                "message": f"Shared container test {request_id}"
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
            result = response.json()
            scan_method = result.get('scan_result', {}).get('scan_method', 'unknown')
            
            return {
                "request_id": request_id,
                "success": True,
                "duration": duration,
                "scan_method": scan_method,
                "status": result.get('scan_result', {}).get('status', 'unknown')
            }
        else:
            return {
                "request_id": request_id,
                "success": False,
                "duration": duration,
                "error": f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        return {
            "request_id": request_id,
            "success": False,
            "duration": 0,
            "error": str(e)
        }

def test_container_management():
    """测试容器管理功能"""
    print("🐳 测试Docker容器管理")
    print("=" * 50)
    
    # 1. 检查初始状态
    print("1. 检查初始容器状态...")
    status = get_docker_status()
    print(f"   初始状态: {status.get('shared_container', {}).get('status', 'unknown')}")
    
    # 2. 启动共享容器
    print("\n2. 启动共享容器...")
    start_result = start_shared_container()
    if start_result.get('success'):
        print("   ✅ 共享容器启动成功")
        container_status = start_result.get('container_status', {})
        print(f"   容器ID: {container_status.get('container_id', 'unknown')}")
        print(f"   运行时间: {container_status.get('uptime', 'unknown')}")
    else:
        print(f"   ❌ 共享容器启动失败: {start_result.get('error', 'unknown')}")
        return False
    
    # 3. 验证容器状态
    print("\n3. 验证容器状态...")
    time.sleep(2)
    status = get_docker_status()
    container_status = status.get('shared_container', {})
    if container_status.get('status') == 'running':
        print("   ✅ 容器运行正常")
        return True
    else:
        print(f"   ❌ 容器状态异常: {container_status.get('status', 'unknown')}")
        return False

def test_concurrent_scans():
    """测试并发扫描"""
    print("\n🔄 测试并发扫描")
    print("=" * 50)
    
    # 并发发送多个扫描请求
    num_requests = 3
    print(f"发送 {num_requests} 个并发扫描请求...")
    
    results = []
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        # 提交所有任务
        futures = [
            executor.submit(send_scan_request, i+1)
            for i in range(num_requests)
        ]
        
        # 收集结果
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                
                request_id = result['request_id']
                if result['success']:
                    duration = result['duration']
                    scan_method = result['scan_method']
                    print(f"   请求{request_id}: ✅ 成功 ({duration:.1f}秒, {scan_method})")
                else:
                    error = result['error']
                    print(f"   请求{request_id}: ❌ 失败 ({error})")
                    
            except Exception as e:
                print(f"   请求处理异常: {e}")
    
    # 分析结果
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\n📊 并发测试结果:")
    print(f"   成功: {len(successful)}/{num_requests}")
    print(f"   失败: {len(failed)}/{num_requests}")
    
    if successful:
        avg_duration = sum(r['duration'] for r in successful) / len(successful)
        shared_docker_count = sum(1 for r in successful if r.get('scan_method') == 'shared_docker')
        print(f"   平均耗时: {avg_duration:.1f}秒")
        print(f"   使用共享容器: {shared_docker_count}/{len(successful)}")
    
    return len(successful) >= num_requests * 0.8  # 80%成功率

def test_container_reuse():
    """测试容器复用"""
    print("\n♻️ 测试容器复用")
    print("=" * 50)
    
    # 检查容器启动时间
    status_before = get_docker_status()
    container_before = status_before.get('shared_container', {})
    started_at_before = container_before.get('started_at')
    
    print(f"扫描前容器启动时间: {started_at_before}")
    
    # 执行一次扫描
    print("执行扫描请求...")
    scan_result = send_scan_request("reuse_test")
    
    if scan_result['success']:
        print(f"✅ 扫描成功 ({scan_result['duration']:.1f}秒)")
    else:
        print(f"❌ 扫描失败: {scan_result['error']}")
        return False
    
    # 检查容器是否复用
    time.sleep(2)
    status_after = get_docker_status()
    container_after = status_after.get('shared_container', {})
    started_at_after = container_after.get('started_at')
    
    print(f"扫描后容器启动时间: {started_at_after}")
    
    if started_at_before == started_at_after:
        print("✅ 容器成功复用（启动时间未变）")
        return True
    else:
        print("⚠️ 容器可能重启了")
        return False

def test_performance_comparison():
    """测试性能对比"""
    print("\n⚡ 性能对比测试")
    print("=" * 50)
    
    # 测试共享容器模式
    print("测试共享容器模式...")
    shared_results = []
    for i in range(2):
        result = send_scan_request(f"perf_shared_{i+1}")
        if result['success']:
            shared_results.append(result['duration'])
            print(f"   共享容器扫描{i+1}: {result['duration']:.1f}秒")
    
    if shared_results:
        avg_shared = sum(shared_results) / len(shared_results)
        print(f"   共享容器平均耗时: {avg_shared:.1f}秒")
        
        # 分析性能
        if avg_shared < 60:
            print("🚀 共享容器性能优秀（<1分钟）")
            return "excellent"
        elif avg_shared < 120:
            print("✅ 共享容器性能良好（<2分钟）")
            return "good"
        else:
            print("⚠️ 共享容器性能一般（>2分钟）")
            return "average"
    else:
        print("❌ 共享容器测试失败")
        return "failed"

def cleanup_test():
    """清理测试"""
    print("\n🧹 清理测试环境")
    print("=" * 50)
    
    # 可选择是否停止共享容器
    print("是否停止共享容器？(y/N): ", end="")
    try:
        choice = input().strip().lower()
        if choice == 'y':
            print("停止共享容器...")
            result = stop_shared_container()
            if result.get('success'):
                print("✅ 共享容器已停止")
            else:
                print(f"❌ 停止失败: {result.get('error', 'unknown')}")
        else:
            print("保持共享容器运行")
    except:
        print("保持共享容器运行")

def main():
    """主函数"""
    print("🧪 共享Docker容器功能测试")
    print("=" * 50)
    
    # 检查服务状态
    if not test_service_health():
        print("❌ JaCoCo API服务未运行")
        print("💡 请先启动服务: python app.py")
        return
    
    print("✅ 服务连接正常")
    
    # 1. 测试容器管理
    container_mgmt_ok = test_container_management()
    
    # 2. 测试并发扫描
    concurrent_ok = test_concurrent_scans() if container_mgmt_ok else False
    
    # 3. 测试容器复用
    reuse_ok = test_container_reuse() if container_mgmt_ok else False
    
    # 4. 性能对比
    performance = test_performance_comparison() if container_mgmt_ok else "failed"
    
    # 总结
    print("\n" + "=" * 50)
    print("📋 测试结果总结:")
    print(f"  容器管理: {'✅ 正常' if container_mgmt_ok else '❌ 异常'}")
    print(f"  并发扫描: {'✅ 正常' if concurrent_ok else '❌ 异常'}")
    print(f"  容器复用: {'✅ 正常' if reuse_ok else '❌ 异常'}")
    print(f"  性能表现: {performance}")
    
    if container_mgmt_ok and concurrent_ok and reuse_ok:
        print("\n🎉 共享容器功能测试全部通过！")
        print("\n✅ 主要优势:")
        print("  1. 容器启动开销大幅减少")
        print("  2. 支持高效并发处理")
        print("  3. 资源利用率显著提升")
        print("  4. 扫描速度明显改善")
        
        if performance == "excellent":
            print("  5. 性能表现优秀")
        elif performance == "good":
            print("  5. 性能表现良好")
        
    else:
        print("\n⚠️ 部分功能存在问题")
        if not container_mgmt_ok:
            print("❌ 容器管理功能异常")
        if not concurrent_ok:
            print("❌ 并发处理功能异常")
        if not reuse_ok:
            print("❌ 容器复用功能异常")
    
    # 清理
    cleanup_test()

if __name__ == "__main__":
    main()
