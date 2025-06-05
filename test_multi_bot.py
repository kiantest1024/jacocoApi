#!/usr/bin/env python3
"""
多机器人配置测试脚本
"""

import sys
import json
from typing import Dict, Any

def test_config():
    """测试配置系统"""
    try:
        from config import (
            get_bot_for_project, 
            get_lark_config, 
            get_service_config,
            list_all_bots,
            list_project_mappings
        )
        
        print("🔧 多机器人配置测试")
        print("=" * 50)
        
        # 1. 测试机器人列表
        print("1. 📋 机器人列表:")
        bots = list_all_bots()
        for bot_id, bot_config in bots.items():
            print(f"   {bot_id}: {bot_config['name']}")
        print(f"   总计: {len(bots)} 个机器人\n")
        
        # 2. 测试项目映射
        print("2. 🗺️ 项目映射规则:")
        mappings = list_project_mappings()
        for pattern, bot_id in mappings.items():
            bot_name = bots.get(bot_id, {}).get('name', '未知机器人')
            print(f"   {pattern} -> {bot_name} ({bot_id})")
        print(f"   总计: {len(mappings)} 个映射规则\n")
        
        # 3. 测试项目匹配
        print("3. 🎯 项目匹配测试:")
        test_cases = [
            ("http://git.example.com/jacocotest.git", "jacocotest"),
            ("http://git.example.com/frontend/web-app.git", "web-app"),
            ("http://git.example.com/backend/user-service.git", "user-service"),
            ("http://git.example.com/team-a/frontend-dashboard.git", "frontend-dashboard"),
            ("http://git.example.com/team-b/backend-api.git", "backend-api"),
            ("http://git.example.com/devops/deploy-scripts.git", "deploy-scripts"),
            ("http://git.example.com/unknown/random-project.git", "random-project"),
        ]
        
        for repo_url, project_name in test_cases:
            bot_id = get_bot_for_project(repo_url, project_name)
            bot_config = get_lark_config(bot_id)
            print(f"   📦 {project_name}")
            print(f"      仓库: {repo_url}")
            print(f"      机器人: {bot_config['name']} ({bot_id})")
            print(f"      Webhook: {bot_config['webhook_url'][:50]}...")
            print()
        
        # 4. 测试完整配置
        print("4. ⚙️ 完整配置测试:")
        test_repo = "http://git.example.com/frontend/test-project.git"
        config = get_service_config(test_repo)
        
        print(f"   项目: {config['service_name']}")
        print(f"   机器人: {config['bot_name']} ({config['bot_id']})")
        print(f"   通知启用: {config['enable_notifications']}")
        print(f"   Docker扫描: {config['use_docker']}")
        print(f"   超时时间: {config['notification_timeout']}s")
        print(f"   重试次数: {config['notification_retry_count']}")
        
        print("\n✅ 配置测试完成")
        return True
        
    except ImportError as e:
        print(f"❌ 导入配置失败: {e}")
        print("请确保 config.py 文件存在且配置正确")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_api_endpoints():
    """测试API接口"""
    try:
        import requests
        
        base_url = "http://localhost:8002"
        
        print("\n🌐 API接口测试")
        print("=" * 50)
        
        # 测试机器人列表接口
        print("1. 测试机器人列表接口:")
        try:
            response = requests.get(f"{base_url}/config/bots", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 成功获取 {data['total_bots']} 个机器人")
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️ 无法连接到服务: {e}")
        
        # 测试项目映射接口
        print("\n2. 测试项目映射接口:")
        try:
            response = requests.get(f"{base_url}/config/mappings", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 成功获取 {data['total_mappings']} 个映射规则")
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️ 无法连接到服务: {e}")
        
        # 测试项目配置测试接口
        print("\n3. 测试项目配置接口:")
        test_projects = ["jacocotest", "frontend-app", "backend-service", "unknown-project"]
        
        for project in test_projects:
            try:
                response = requests.get(f"{base_url}/config/test/{project}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ {project} -> {data['bot_config']['name']}")
                else:
                    print(f"   ❌ {project} 测试失败: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️ 无法连接到服务: {e}")
                break
        
        print("\n✅ API测试完成")
        
    except ImportError:
        print("\n⚠️ requests库未安装，跳过API测试")
        print("安装命令: pip install requests")

def main():
    """主函数"""
    print("🚀 JaCoCo多机器人配置测试工具")
    print("=" * 60)
    
    # 测试配置
    config_ok = test_config()
    
    if config_ok:
        # 测试API接口
        test_api_endpoints()
        
        print("\n📖 使用说明:")
        print("1. 启动服务: python app.py")
        print("2. 查看机器人: http://localhost:8002/config/bots")
        print("3. 查看映射: http://localhost:8002/config/mappings")
        print("4. 测试项目: http://localhost:8002/config/test/{project_name}")
        print("5. API文档: http://localhost:8002/docs")
        
        print("\n🔧 配置文件:")
        print("- 当前配置: config.py")
        print("- 示例配置: config_example.py")
        print("- 复制示例: cp config_example.py config.py")
    else:
        print("\n❌ 配置测试失败，请检查配置文件")
        sys.exit(1)

if __name__ == "__main__":
    main()
