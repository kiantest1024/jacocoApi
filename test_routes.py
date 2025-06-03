#!/usr/bin/env python3
"""
测试所有可用路由的脚本。
"""

import json
import requests


def test_all_routes():
    """测试所有可用的路由。"""
    
    base_url = "http://localhost:8001"
    
    routes_to_test = [
        # 基础路由
        ("GET", "/health", "健康检查"),
        ("GET", "/docs", "API 文档"),
        ("GET", "/openapi.json", "OpenAPI 架构"),
        
        # GitHub webhook 路由
        ("GET", "/github/test", "GitHub webhook 测试"),
        ("POST", "/github/webhook", "GitHub webhook 接收"),
        
        # API 路由 (需要认证)
        # ("GET", "/api/...", "API 端点"),
    ]
    
    print("=== 测试所有可用路由 ===\n")
    
    for method, path, description in routes_to_test:
        full_url = f"{base_url}{path}"
        print(f"测试 {method} {path} ({description})")
        
        try:
            if method == "GET":
                response = requests.get(full_url, timeout=5)
            elif method == "POST":
                # 对于 POST 路由，发送测试数据
                if path == "/github/webhook":
                    test_payload = {
                        "object_kind": "push",
                        "ref": "refs/heads/develop",
                        "user_name": "Kian",
                        "project": {"name": "jacocoTest"},
                        "commits": [{
                            "id": "abc123def456",
                            "message": "Fix login bug"
                        }]
                    }
                    response = requests.post(full_url, json=test_payload, timeout=5)
                else:
                    response = requests.post(full_url, json={}, timeout=5)
            
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 404:
                print(f"  ❌ 路由不存在")
            elif response.status_code < 400:
                print(f"  ✅ 路由可用")
                if response.headers.get('content-type', '').startswith('application/json'):
                    try:
                        result = response.json()
                        if isinstance(result, dict) and 'message' in result:
                            print(f"  📝 消息: {result['message']}")
                    except:
                        pass
            else:
                print(f"  ⚠️ 路由存在但返回错误")
                try:
                    error = response.json()
                    if isinstance(error, dict) and 'message' in error:
                        print(f"  📝 错误: {error['message']}")
                except:
                    pass
                    
        except requests.exceptions.ConnectionError:
            print(f"  ❌ 连接失败 - 服务可能未运行")
        except requests.exceptions.Timeout:
            print(f"  ❌ 请求超时")
        except Exception as e:
            print(f"  ❌ 异常: {str(e)}")
        
        print()


def test_specific_webhook():
    """专门测试您的 webhook 请求。"""
    
    print("=== 专门测试您的 GitLab Webhook ===\n")
    
    # 测试不同的可能路径
    possible_paths = [
        "/github/webhook",
        "/webhook", 
        "/scan-trigger",
        "/api/webhook"
    ]
    
    payload = {
        "object_kind": "push",
        "ref": "refs/heads/develop",
        "user_name": "Kian",
        "project": {"name": "jacocoTest"},
        "commits": [{
            "id": "abc123def456",
            "message": "Fix login bug"
        }]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    for path in possible_paths:
        url = f"http://localhost:8001{path}"
        print(f"测试路径: {path}")
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 404:
                print(f"  ❌ 路径不存在")
            else:
                print(f"  ✅ 路径存在")
                try:
                    result = response.json()
                    print(f"  📝 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                except:
                    print(f"  📝 响应: {response.text}")
                    
        except requests.exceptions.ConnectionError:
            print(f"  ❌ 连接失败")
        except Exception as e:
            print(f"  ❌ 异常: {str(e)}")
        
        print()


def check_service_status():
    """检查服务状态。"""
    
    print("=== 检查服务状态 ===\n")
    
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print("✅ 服务正在运行")
            print(f"📝 版本: {result.get('version', 'unknown')}")
            print(f"📝 状态: {result.get('status', 'unknown')}")
            return True
        else:
            print(f"⚠️ 服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务 - 请确保服务在 http://localhost:8001 上运行")
        return False
    except Exception as e:
        print(f"❌ 检查服务时出错: {str(e)}")
        return False


if __name__ == "__main__":
    print("========================================")
    print("路由测试工具")
    print("========================================\n")
    
    # 首先检查服务状态
    if check_service_status():
        print()
        
        # 测试所有路由
        test_all_routes()
        
        # 专门测试 webhook
        test_specific_webhook()
    
    print("========================================")
    print("测试完成")
    print("========================================")
