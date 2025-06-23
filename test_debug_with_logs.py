#!/usr/bin/env python3
"""测试调试版本并获取详细日志"""

import requests
import json
import time

def test_debug_with_detailed_logs():
    """测试调试版本并获取详细日志"""
    
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
    
    print("🧪 测试调试版本 - 详细日志模式")
    print("=" * 50)
    
    # 先清空之前的日志
    try:
        clear_response = requests.delete("http://localhost:8003/debug/logs", timeout=5)
        if clear_response.status_code == 200:
            print("🧹 已清空之前的日志")
    except:
        pass
    
    start_time = time.time()
    
    print("🚀 发送扫描请求...")
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️  总耗时: {duration:.1f}秒")
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功")
            
            # 显示基本信息
            print(f"📋 状态: {result.get('status', 'unknown')}")
            print(f"🔍 扫描方法: {result.get('debug_info', {}).get('scan_method', 'unknown')}")
            
            # 显示扫描分析
            if "debug_info" in result and "scan_analysis" in result["debug_info"]:
                analysis = result["debug_info"]["scan_analysis"]
                print(f"\n📊 扫描分析:")
                print(f"   测试运行: {analysis.get('tests_run', 0)}")
                print(f"   测试失败: {analysis.get('tests_failed', 0)}")
                print(f"   编译错误: {len(analysis.get('compilation_errors', []))}")
                
                # 显示编译错误
                if analysis.get('compilation_errors'):
                    print(f"\n🔴 编译错误:")
                    for error in analysis['compilation_errors'][:3]:
                        print(f"   {error}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"📋 响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 请求异常: {e}")
        return False
    
    # 获取详细日志
    print("\n" + "="*50)
    print("📝 获取详细执行日志")
    print("="*50)
    
    try:
        logs_response = requests.get("http://localhost:8003/debug/logs", timeout=10)
        if logs_response.status_code == 200:
            logs_data = logs_response.json()
            logs = logs_data.get('logs', [])
            
            print(f"📊 日志总行数: {len(logs)}")
            
            # 查找关键信息
            key_patterns = [
                'pom.xml',
                'jacoco',
                'Maven',
                'test',
                'ERROR',
                'WARNING',
                'BUILD',
                '增强',
                '备份'
            ]
            
            print("\n🔍 关键日志信息:")
            for log_line in logs:
                if any(pattern.lower() in log_line.lower() for pattern in key_patterns):
                    # 清理日志格式
                    clean_line = log_line.replace('\\n', '').strip()
                    if clean_line:
                        print(f"   {clean_line}")
            
            # 显示最后几行日志
            print(f"\n📝 最后10行日志:")
            for log_line in logs[-10:]:
                clean_line = log_line.replace('\\n', '').strip()
                if clean_line:
                    print(f"   {clean_line}")
        else:
            print(f"❌ 获取日志失败: {logs_response.status_code}")
    
    except Exception as e:
        print(f"💥 获取日志异常: {e}")
    
    return True

def main():
    """主函数"""
    
    # 检查服务状态
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
    
    print("\n" + "=" * 50)
    
    # 运行测试
    success = test_debug_with_detailed_logs()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 测试完成！请查看上面的详细日志分析。")
    else:
        print("⚠️  测试遇到问题。")
    
    print("\n💡 分析要点:")
    print("- 检查是否有 'pom.xml 增强' 相关日志")
    print("- 查看是否有 Maven 执行错误")
    print("- 确认测试是否真正运行")
    print("- 检查 JaCoCo 插件是否被识别")

if __name__ == "__main__":
    main()
