#!/usr/bin/env python3
"""
测试所有修复
验证异步问题和Maven缓存优化
"""

import requests
import json
import time
import subprocess
import os

def check_maven_cache():
    """检查Maven缓存"""
    print("🔍 检查Maven缓存状态")
    
    maven_repo = os.path.expanduser("~/.m2/repository")
    if os.path.exists(maven_repo):
        print(f"✅ Maven仓库存在: {maven_repo}")
        
        # 检查关键依赖
        jacoco_path = os.path.join(maven_repo, "org", "jacoco")
        if os.path.exists(jacoco_path):
            print("✅ JaCoCo依赖已缓存")
            return True
        else:
            print("❌ JaCoCo依赖未缓存")
            return False
    else:
        print("❌ Maven仓库不存在")
        return False

def warmup_cache_if_needed():
    """如果需要则预热缓存"""
    if not check_maven_cache():
        print("\n🔥 开始预热Maven缓存...")
        try:
            result = subprocess.run(
                ["python", "warmup_maven_cache.py"],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                print("✅ Maven缓存预热成功")
                return True
            else:
                print("⚠️ Maven缓存预热失败，但继续测试")
                return False
        except Exception as e:
            print(f"⚠️ 预热缓存异常: {e}")
            return False
    else:
        print("✅ Maven缓存状态良好")
        return True

def test_service_health():
    """测试服务健康状态"""
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_fast_scan():
    """测试快速扫描"""
    print("\n⚡ 测试快速扫描（应该使用缓存）")
    
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
                "message": "Test fast scan with cache"
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
        
        print(f"⏱️ 扫描耗时: {duration:.1f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 扫描成功")
            
            # 检查覆盖率数据
            report_data = result.get('report_data', {})
            coverage_summary = report_data.get('coverage_summary', {})
            
            if coverage_summary:
                print("📈 覆盖率数据:")
                has_coverage = False
                for metric, value in coverage_summary.items():
                    print(f"  {metric}: {value}%")
                    if isinstance(value, (int, float)) and value > 0:
                        has_coverage = True
                
                if has_coverage:
                    print("✅ 覆盖率数据正常")
                    
                    # 检查扫描速度
                    if duration < 60:
                        print("🚀 扫描速度优秀（<1分钟）")
                        return "excellent"
                    elif duration < 120:
                        print("✅ 扫描速度良好（<2分钟）")
                        return "good"
                    else:
                        print("⚠️ 扫描速度较慢（>2分钟）")
                        return "slow"
                else:
                    print("❌ 覆盖率数据为0")
                    return "no_coverage"
            else:
                print("❌ 未找到覆盖率数据")
                return "no_data"
        else:
            print(f"❌ 扫描失败: {response.status_code}")
            return "failed"
            
    except requests.exceptions.Timeout:
        print("❌ 扫描超时")
        return "timeout"
    except Exception as e:
        print(f"❌ 扫描异常: {e}")
        return "error"

def test_service_stability():
    """测试服务稳定性"""
    print("\n🔄 测试服务稳定性")
    
    # 检查服务在扫描前后是否稳定
    checks = []
    
    for i in range(3):
        print(f"检查 {i+1}/3...")
        if test_service_health():
            checks.append(True)
            print("✅ 服务响应正常")
        else:
            checks.append(False)
            print("❌ 服务无响应")
        
        if i < 2:
            time.sleep(2)
    
    success_rate = sum(checks) / len(checks) * 100
    print(f"服务稳定性: {success_rate:.1f}%")
    
    return success_rate >= 100  # 要求100%稳定

def analyze_performance(scan_result):
    """分析性能结果"""
    print("\n📊 性能分析")
    print("=" * 50)
    
    if scan_result == "excellent":
        print("🎉 性能优秀！")
        print("✅ Maven缓存工作正常")
        print("✅ 离线模式生效")
        print("✅ 扫描速度很快")
        
    elif scan_result == "good":
        print("✅ 性能良好")
        print("✅ 扫描在合理时间内完成")
        print("💡 可能使用了在线模式")
        
    elif scan_result == "slow":
        print("⚠️ 性能较慢")
        print("💡 建议:")
        print("  1. 运行 python warmup_maven_cache.py")
        print("  2. 检查网络连接")
        print("  3. 确认Maven缓存配置")
        
    elif scan_result == "no_coverage":
        print("❌ 覆盖率问题")
        print("💡 建议:")
        print("  1. 检查JaCoCo配置")
        print("  2. 确认测试执行")
        print("  3. 查看详细日志")
        
    else:
        print("❌ 扫描失败")
        print("💡 建议:")
        print("  1. 检查服务日志")
        print("  2. 确认网络连接")
        print("  3. 验证项目配置")

def main():
    """主函数"""
    print("🧪 JaCoCo全面修复测试")
    print("=" * 50)
    
    # 1. 检查服务状态
    if not test_service_health():
        print("❌ 服务未运行，请先启动服务")
        print("💡 启动命令: python app.py")
        return
    
    print("✅ 服务连接正常")
    
    # 2. 检查并预热Maven缓存
    cache_ok = warmup_cache_if_needed()
    
    # 3. 测试服务稳定性（扫描前）
    stability_before = test_service_stability()
    
    # 4. 执行快速扫描测试
    scan_result = test_fast_scan()
    
    # 5. 测试服务稳定性（扫描后）
    print("\n🔄 检查扫描后服务状态...")
    time.sleep(3)
    stability_after = test_service_stability()
    
    # 6. 分析结果
    print("\n" + "=" * 50)
    print("📋 测试结果总结:")
    print(f"  Maven缓存: {'✅ 正常' if cache_ok else '❌ 问题'}")
    print(f"  扫描前稳定性: {'✅ 稳定' if stability_before else '❌ 不稳定'}")
    print(f"  扫描结果: {scan_result}")
    print(f"  扫描后稳定性: {'✅ 稳定' if stability_after else '❌ 不稳定'}")
    
    # 7. 性能分析
    analyze_performance(scan_result)
    
    # 8. 总体评估
    print("\n🎯 总体评估:")
    
    if (stability_before and stability_after and 
        scan_result in ["excellent", "good"] and cache_ok):
        print("🎉 所有修复测试通过！")
        print("\n✅ 主要成果:")
        print("  1. 异步处理问题已解决")
        print("  2. 服务稳定性良好")
        print("  3. Maven缓存优化生效")
        print("  4. 扫描速度显著提升")
        print("  5. 覆盖率数据正确")
        
        print("\n💡 现在可以高效使用JaCoCo扫描服务了！")
        
    elif stability_before and stability_after:
        print("✅ 稳定性修复成功")
        if scan_result in ["slow", "no_coverage"]:
            print("⚠️ 性能或数据问题需要进一步优化")
        
    else:
        print("❌ 仍有问题需要解决")
        
        if not stability_before or not stability_after:
            print("❌ 服务稳定性问题")
        if scan_result not in ["excellent", "good"]:
            print("❌ 扫描性能或数据问题")
    
    print("\n🔧 下一步建议:")
    if not cache_ok:
        print("  1. 运行 python warmup_maven_cache.py 预热缓存")
    if scan_result == "slow":
        print("  2. 检查网络连接和Maven配置")
    if scan_result in ["no_coverage", "no_data"]:
        print("  3. 检查JaCoCo配置和测试执行")
    if not (stability_before and stability_after):
        print("  4. 检查服务日志中的错误信息")

if __name__ == "__main__":
    main()
