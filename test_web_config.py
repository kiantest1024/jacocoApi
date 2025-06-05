#!/usr/bin/env python3
"""
Web配置界面测试脚本
"""

import requests
import json
import time

def test_web_interface():
    """测试Web配置界面"""
    base_url = "http://localhost:8002"
    
    print("🌐 Web配置界面测试")
    print("=" * 50)
    
    try:
        # 1. 测试配置页面
        print("1. 测试配置页面访问...")
        response = requests.get(f"{base_url}/config", timeout=5)
        if response.status_code == 200:
            print("   ✅ 配置页面访问成功")
            print(f"   📄 页面大小: {len(response.text)} 字符")
        else:
            print(f"   ❌ 配置页面访问失败: {response.status_code}")
            return False
        
        # 2. 测试机器人列表API
        print("\n2. 测试机器人列表API...")
        response = requests.get(f"{base_url}/config/bots", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功获取 {data['total_bots']} 个机器人")
            for bot_id, bot_config in data['bots'].items():
                print(f"      - {bot_id}: {bot_config['name']}")
        else:
            print(f"   ❌ 机器人列表API失败: {response.status_code}")
        
        # 3. 测试项目映射API
        print("\n3. 测试项目映射API...")
        response = requests.get(f"{base_url}/config/mappings", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功获取 {data['total_mappings']} 个映射规则")
            for pattern, bot_id in list(data['mappings'].items())[:3]:
                print(f"      - {pattern} -> {bot_id}")
        else:
            print(f"   ❌ 项目映射API失败: {response.status_code}")
        
        # 4. 测试项目配置测试API
        print("\n4. 测试项目配置API...")
        test_projects = ["jacocotest", "frontend-app", "backend-service"]
        
        for project in test_projects:
            response = requests.get(f"{base_url}/config/test/{project}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {project} -> {data['bot_config']['name']}")
            else:
                print(f"   ❌ {project} 测试失败: {response.status_code}")
        
        # 5. 测试保存配置API
        print("\n5. 测试保存配置API...")
        test_mapping = {
            "project_name": "test-web-project",
            "git_url": "http://git.example.com/test/web-project.git",
            "bot_id": "default",
            "webhook_url": ""
        }
        
        response = requests.post(
            f"{base_url}/config/mapping",
            json=test_mapping,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 配置保存成功: {data['message']}")
            
            # 6. 测试删除配置API
            print("\n6. 测试删除配置API...")
            delete_request = {"pattern": "test-web-project"}
            
            response = requests.delete(
                f"{base_url}/config/mapping",
                json=delete_request,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 配置删除成功: {data['message']}")
            else:
                print(f"   ❌ 配置删除失败: {response.status_code}")
        else:
            print(f"   ❌ 配置保存失败: {response.status_code}")
        
        print("\n✅ Web界面测试完成")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络连接失败: {e}")
        print("请确保服务已启动: python app.py")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_web_ui_features():
    """测试Web界面功能"""
    print("\n🎨 Web界面功能说明")
    print("=" * 50)
    
    features = [
        "📝 Git地址输入和项目名称自动提取",
        "🤖 机器人选择和Webhook URL自动填充",
        "💾 项目配置保存和立即生效",
        "🧪 项目配置测试功能",
        "📋 当前配置列表和管理",
        "🔄 实时数据刷新",
        "🗑️ 配置删除功能",
        "📊 机器人状态监控",
    ]
    
    for feature in features:
        print(f"   {feature}")
    
    print("\n🌐 访问地址:")
    print("   配置管理: http://localhost:8002/config")
    print("   API文档: http://localhost:8002/docs")
    print("   健康检查: http://localhost:8002/health")

def main():
    """主函数"""
    print("🚀 JaCoCo Web配置界面测试工具")
    print("=" * 60)
    
    # 测试Web界面
    success = test_web_interface()
    
    # 显示功能说明
    test_web_ui_features()
    
    if success:
        print("\n📖 使用说明:")
        print("1. 启动服务: python app.py")
        print("2. 访问配置页面: http://localhost:8002/config")
        print("3. 输入Git地址，自动提取项目名称")
        print("4. 选择Lark机器人，自动填充Webhook URL")
        print("5. 保存配置，立即生效")
        print("6. 测试配置，验证映射关系")
        
        print("\n🎯 配置流程:")
        print("Git地址 → 项目名称 → 选择机器人 → 保存配置 → 立即生效")
    else:
        print("\n❌ Web界面测试失败，请检查服务状态")

if __name__ == "__main__":
    main()
