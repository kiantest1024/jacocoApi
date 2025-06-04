#!/usr/bin/env python3
"""
测试覆盖率修复效果
验证Java项目是否恢复正常的覆盖率
"""

import requests
import json
import time

def test_known_java_project():
    """测试已知的Java项目"""
    print("🧪 测试已知Java项目覆盖率修复")
    print("=" * 60)
    
    # 测试jacocoTest项目（之前有覆盖率的项目）
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": "jacocoTest",
            "http_url": "https://gitlab.complexdevops.com/kian/jacocoTest.git"
        },
        "user_name": "test_user",
        "commits": [
            {
                "id": "main",
                "message": "Test coverage fix"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    print(f"📤 测试项目: {webhook_data['project']['name']}")
    print(f"仓库: {webhook_data['project']['http_url']}")
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8002/github/webhook-no-auth",
            json=webhook_data,
            timeout=300
        )
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ 处理时间: {duration:.1f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook处理成功")
            
            # 分析结果
            scan_result = result.get('scan_result', {})
            report_data = result.get('report_data', {})
            
            print(f"\n📊 扫描结果:")
            print(f"  状态: {scan_result.get('status')}")
            print(f"  方法: {scan_result.get('scan_method')}")
            print(f"  返回码: {scan_result.get('return_code')}")
            
            # 检查Maven输出
            maven_output = scan_result.get('maven_output', '')
            if "BUILD SUCCESS" in maven_output:
                print("✅ Maven构建成功")
            elif "BUILD FAILURE" in maven_output:
                print("❌ Maven构建失败")
            
            # 检查测试执行
            if "Tests run:" in maven_output:
                print("✅ 检测到测试执行")
                test_lines = [line for line in maven_output.split('\n') if 'Tests run:' in line]
                for line in test_lines:
                    print(f"  {line.strip()}")
            else:
                print("⚠️ 未检测到测试执行")
            
            # 检查JaCoCo执行
            if "jacoco:report" in maven_output.lower():
                print("✅ JaCoCo报告生成")
            else:
                print("⚠️ 未检测到JaCoCo报告生成")
            
            # 检查覆盖率数据
            coverage_summary = report_data.get('coverage_summary', {})
            if coverage_summary:
                print(f"\n📈 覆盖率结果:")
                total_coverage = 0
                count = 0
                for metric, value in coverage_summary.items():
                    print(f"  {metric}: {value}%")
                    if isinstance(value, (int, float)) and value > 0:
                        total_coverage += value
                        count += 1
                
                if count > 0:
                    avg_coverage = total_coverage / count
                    if avg_coverage > 0:
                        print(f"✅ 覆盖率修复成功！平均覆盖率: {avg_coverage:.1f}%")
                        return True
                    else:
                        print("❌ 覆盖率仍然为0%")
                        return False
                else:
                    print("❌ 所有覆盖率指标都为0%")
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

def test_lotto_game_project():
    """测试lotto-game项目"""
    print("\n🎲 测试backend-lotto-game项目")
    print("=" * 60)
    
    webhook_data = {
        "object_kind": "push",
        "project": {
            "name": "backend-lotto-game",
            "http_url": "http://172.16.1.30/kian/backend-lotto-game.git"
        },
        "user_name": "test_user",
        "commits": [
            {
                "id": "main",
                "message": "Test lotto game coverage"
            }
        ],
        "ref": "refs/heads/main"
    }
    
    print(f"📤 测试项目: {webhook_data['project']['name']}")
    
    try:
        response = requests.post(
            "http://localhost:8002/github/webhook-no-auth",
            json=webhook_data,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 分析结果
            scan_result = result.get('scan_result', {})
            report_data = result.get('report_data', {})
            
            print(f"📊 扫描结果:")
            print(f"  状态: {scan_result.get('status')}")
            
            # 检查源代码检测
            if "主代码=True" in str(result):
                print("✅ 检测到主代码")
            if "测试代码=True" in str(result):
                print("✅ 检测到测试代码")
            
            # 检查覆盖率
            coverage_summary = report_data.get('coverage_summary', {})
            if coverage_summary:
                print(f"📈 覆盖率:")
                has_coverage = False
                for metric, value in coverage_summary.items():
                    print(f"  {metric}: {value}%")
                    if isinstance(value, (int, float)) and value > 0:
                        has_coverage = True
                
                if has_coverage:
                    print("✅ lotto-game项目有覆盖率数据")
                    return True
                else:
                    print("⚠️ lotto-game项目覆盖率仍为0%")
                    return False
            else:
                print("❌ lotto-game项目无覆盖率数据")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def analyze_results(jacoco_test_success, lotto_game_success):
    """分析测试结果"""
    print("\n📋 测试结果分析")
    print("=" * 60)
    
    print(f"jacocoTest项目: {'✅ 成功' if jacoco_test_success else '❌ 失败'}")
    print(f"lotto-game项目: {'✅ 成功' if lotto_game_success else '❌ 失败'}")
    
    if jacoco_test_success and lotto_game_success:
        print("\n🎉 所有项目覆盖率修复成功！")
        print("✅ JaCoCo配置已恢复正常")
        print("✅ Java项目可以正常生成覆盖率报告")
    elif jacoco_test_success:
        print("\n⚠️ 部分修复成功")
        print("✅ jacocoTest项目恢复正常")
        print("❌ lotto-game项目仍有问题，可能需要进一步调试")
    elif lotto_game_success:
        print("\n⚠️ 部分修复成功")
        print("❌ jacocoTest项目仍有问题")
        print("✅ lotto-game项目恢复正常")
    else:
        print("\n❌ 修复失败")
        print("两个项目的覆盖率都仍然为0%")
        print("需要进一步分析Maven输出和JaCoCo配置")

def main():
    """主函数"""
    print("🔧 JaCoCo覆盖率修复测试")
    print("=" * 60)
    print("测试目标:")
    print("1. 验证之前有覆盖率的项目是否恢复正常")
    print("2. 验证新的Java项目是否能正确生成覆盖率")
    print("3. 确认JaCoCo配置修复是否成功")
    
    # 测试两个项目
    jacoco_test_success = test_known_java_project()
    lotto_game_success = test_lotto_game_project()
    
    # 分析结果
    analyze_results(jacoco_test_success, lotto_game_success)
    
    if not (jacoco_test_success or lotto_game_success):
        print("\n🔍 进一步调试建议:")
        print("1. 检查Maven输出中的详细错误信息")
        print("2. 验证JaCoCo插件是否正确执行")
        print("3. 检查测试是否实际运行")
        print("4. 确认项目结构是否正确")

if __name__ == "__main__":
    main()
