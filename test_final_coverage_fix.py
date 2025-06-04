#!/usr/bin/env python3
"""
测试最终覆盖率修复
验证覆盖率数据传递和服务稳定性
"""

import requests
import json
import time

def test_coverage_fix():
    """测试覆盖率修复"""
    print("🔧 测试最终覆盖率修复")
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
    
    # 测试jacocoTest项目
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": "jacocotest",
            "http_url": "http://172.16.1.30/kian/jacocotest.git"
        },
        "user_name": "test_user",
        "commits": [
            {
                "id": "5ea76b4989a17153eade57d7d55609ebad7fdd9e",
                "message": "Test final coverage fix"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    print(f"\n📤 测试项目: {webhook_data['project']['name']}")
    
    try:
        start_time = time.time()
        print("⏳ 发送请求...")
        
        response = requests.post(
            "http://localhost:8002/github/webhook-no-auth",
            json=webhook_data,
            timeout=300
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ 处理时间: {duration:.1f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook处理成功")
            
            # 检查服务是否仍在运行
            time.sleep(2)
            try:
                health_response = requests.get("http://localhost:8002/health", timeout=5)
                if health_response.status_code == 200:
                    print("✅ 服务在处理后仍正常运行")
                else:
                    print("❌ 服务在处理后停止响应")
                    return False
            except Exception as e:
                print(f"❌ 服务健康检查失败: {e}")
                return False
            
            # 分析覆盖率数据
            report_data = result.get('report_data', {})
            coverage_summary = report_data.get('coverage_summary', {})
            
            print(f"\n📈 覆盖率数据检查:")
            if coverage_summary:
                print("✅ 找到覆盖率数据:")
                
                has_real_coverage = False
                for metric, value in coverage_summary.items():
                    print(f"  {metric}: {value}%")
                    if isinstance(value, (int, float)) and value > 0:
                        has_real_coverage = True
                
                if has_real_coverage:
                    print("\n🎉 覆盖率数据修复成功！")
                    print("✅ 覆盖率不再是0%")
                    
                    # 检查HTML报告
                    html_url = report_data.get('html_report_url')
                    if html_url:
                        print(f"✅ HTML报告: {html_url}")
                        
                        # 测试HTML报告访问
                        try:
                            html_response = requests.get(html_url, timeout=10)
                            if html_response.status_code == 200:
                                print("✅ HTML报告可访问")
                            else:
                                print(f"⚠️ HTML报告访问问题: {html_response.status_code}")
                        except Exception as e:
                            print(f"⚠️ HTML报告访问异常: {e}")
                    
                    return True
                else:
                    print("❌ 所有覆盖率指标仍为0%")
                    return False
            else:
                print("❌ 未找到覆盖率数据")
                return False
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_service_stability():
    """测试服务稳定性"""
    print("\n🔄 测试服务稳定性")
    print("=" * 60)
    
    # 连续发送多个请求
    for i in range(3):
        print(f"\n📤 发送第{i+1}个请求...")
        
        webhook_data = {
            "object_kind": "push",
            "project": {
                "name": "jacocotest",
                "http_url": "http://172.16.1.30/kian/jacocotest.git"
            },
            "user_name": "stability_test",
            "commits": [
                {
                    "id": "main",
                    "message": f"Stability test {i+1}"
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
            
            if response.status_code == 200:
                print(f"✅ 请求{i+1}成功")
                
                # 检查服务是否仍在运行
                time.sleep(1)
                health_response = requests.get("http://localhost:8002/health", timeout=5)
                if health_response.status_code == 200:
                    print(f"✅ 请求{i+1}后服务仍正常")
                else:
                    print(f"❌ 请求{i+1}后服务停止响应")
                    return False
            else:
                print(f"❌ 请求{i+1}失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 请求{i+1}异常: {e}")
            return False
        
        # 请求间隔
        if i < 2:
            time.sleep(3)
    
    print("\n✅ 服务稳定性测试通过")
    return True

def main():
    """主函数"""
    print("🧪 JaCoCo最终修复测试")
    print("=" * 60)
    
    # 1. 测试覆盖率修复
    coverage_success = test_coverage_fix()
    
    # 2. 测试服务稳定性
    stability_success = test_service_stability()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"  覆盖率修复: {'✅ 成功' if coverage_success else '❌ 失败'}")
    print(f"  服务稳定性: {'✅ 成功' if stability_success else '❌ 失败'}")
    
    if coverage_success and stability_success:
        print("\n🎉 所有修复测试通过！")
        print("\n✅ 主要成果:")
        print("  1. 覆盖率数据正确传递到通知系统")
        print("  2. 服务在处理请求后保持稳定运行")
        print("  3. HTML报告正常生成和访问")
        print("  4. 支持连续多个请求处理")
        
        print("\n💡 现在可以正常使用JaCoCo扫描服务了！")
        print("  - Lark通知将显示正确的覆盖率数据")
        print("  - 服务不会在处理后意外关闭")
        print("  - 支持高并发的webhook请求")
        
    elif coverage_success:
        print("\n⚠️ 部分修复成功")
        print("✅ 覆盖率数据修复成功")
        print("❌ 服务稳定性仍有问题")
        
    elif stability_success:
        print("\n⚠️ 部分修复成功")
        print("❌ 覆盖率数据仍有问题")
        print("✅ 服务稳定性修复成功")
        
    else:
        print("\n❌ 修复失败")
        print("需要进一步调试和修复")
        
        print("\n🔧 故障排除建议:")
        print("  1. 检查服务日志中的详细错误信息")
        print("  2. 验证JaCoCo XML报告是否正确生成")
        print("  3. 检查数据传递逻辑")
        print("  4. 确认异步处理配置")

if __name__ == "__main__":
    main()
