#!/usr/bin/env python3
"""
Linux环境快速修复脚本
解决数据不一致和通知问题
"""

import os
import sys
import requests
import json
import subprocess
import time

def setup_environment():
    """设置环境变量"""
    print("🔧 设置环境变量...")
    
    # 设置环境变量
    env_vars = {
        'CONFIG_STORAGE_TYPE': 'mysql',
        'MYSQL_HOST': '172.16.1.30',
        'MYSQL_PORT': '3306',
        'MYSQL_DATABASE': 'jacoco_config',
        'MYSQL_USER': 'jacoco',
        'MYSQL_PASSWORD': 'asd301325..'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   {key}={value}")
    
    print("✅ 环境变量设置完成")

def wait_for_service():
    """等待服务启动"""
    print("⏳ 等待服务启动...")
    
    for i in range(30):  # 等待最多30秒
        try:
            response = requests.get('http://localhost:8002/health', timeout=2)
            if response.status_code == 200:
                print("✅ 服务已启动")
                return True
        except:
            pass
        
        time.sleep(1)
        if i % 5 == 0:
            print(f"   等待中... ({i+1}/30)")
    
    print("❌ 服务启动超时")
    return False

def sync_project_configs():
    """同步项目配置"""
    print("🔄 同步项目配置...")
    
    projects = [
        {
            "project_name": "jacocotest",
            "git_url": "http://172.16.1.30/kian/jacocotest.git",
            "bot_id": "default"
        },
        {
            "project_name": "backend-lotto-game",
            "git_url": "http://172.16.1.30/kian/backend-lotto-game.git",
            "bot_id": "default"
        }
    ]
    
    for project in projects:
        try:
            response = requests.post(
                'http://localhost:8002/config/mapping',
                json=project,
                timeout=10
            )
            if response.status_code == 200:
                print(f"✅ 添加项目: {project['project_name']}")
            else:
                print(f"⚠️  项目 {project['project_name']}: {response.status_code}")
        except Exception as e:
            print(f"❌ 添加项目 {project['project_name']} 失败: {e}")

def test_webhook():
    """测试webhook功能"""
    print("🧪 测试webhook功能...")
    
    payload = {
        "object_kind": "push",
        "event_name": "push",
        "before": "0000000000000000000000000000000000000000",
        "after": "test123456789",
        "ref": "refs/heads/master",
        "checkout_sha": "test123456789",
        "user_id": 1,
        "user_name": "kian",
        "user_username": "kian",
        "user_email": "kian@example.com",
        "project_id": 1,
        "project": {
            "id": 1,
            "name": "jacocotest",
            "description": "JaCoCo测试项目",
            "web_url": "http://172.16.1.30/kian/jacocotest",
            "git_http_url": "http://172.16.1.30/kian/jacocotest.git",
            "namespace": "kian",
            "path_with_namespace": "kian/jacocotest",
            "default_branch": "master"
        },
        "commits": [
            {
                "id": "test123456789",
                "message": "Test commit for Linux webhook",
                "timestamp": "2024-01-15T10:30:00+00:00",
                "author": {
                    "name": "kian",
                    "email": "kian@example.com"
                }
            }
        ],
        "total_commits_count": 1,
        "repository": {
            "name": "jacocotest",
            "git_http_url": "http://172.16.1.30/kian/jacocotest.git",
            "homepage": "http://172.16.1.30/kian/jacocotest"
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Gitlab-Event': 'Push Hook',
        'User-Agent': 'GitLab/14.0.0'
    }
    
    try:
        print("📡 发送webhook请求...")
        response = requests.post(
            'http://localhost:8002/github/webhook-no-auth',
            json=payload,
            headers=headers,
            timeout=60
        )
        
        print(f"📡 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook处理成功")
            print(f"   请求ID: {result.get('request_id')}")
            print(f"   事件类型: {result.get('event_type')}")
            
            # 检查扫描结果
            scan_result = result.get('scan_result', {})
            scan_status = scan_result.get('status', 'unknown')
            print(f"   扫描状态: {scan_status}")
            
            if scan_status == 'error':
                error_msg = scan_result.get('message', 'Unknown error')
                print(f"   扫描错误: {error_msg}")
                
                # 检查是否是环境问题
                if 'git' in error_msg.lower() or 'mvn' in error_msg.lower():
                    print("   💡 可能是Git或Maven环境问题")
                elif 'docker' in error_msg.lower():
                    print("   💡 可能是Docker环境问题")
            elif scan_status == 'completed':
                print("   ✅ 扫描完成")
                
                # 检查通知
                notification = result.get('notification_result', {})
                if notification:
                    notif_status = notification.get('status', 'unknown')
                    print(f"   通知状态: {notif_status}")
                    
                    if notif_status == 'success':
                        print("   ✅ 通知发送成功")
                    elif notif_status == 'error':
                        print(f"   ❌ 通知失败: {notification.get('message', 'Unknown')}")
                else:
                    print("   ⚠️  没有通知结果")
            
        else:
            print(f"❌ Webhook处理失败: {response.status_code}")
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"❌ Webhook测试失败: {e}")

def check_tools():
    """检查必要工具"""
    print("🔍 检查必要工具...")
    
    tools = {
        'git': ['git', '--version'],
        'maven': ['mvn', '--version'],
        'java': ['java', '-version'],
        'docker': ['docker', '--version']
    }
    
    for tool_name, cmd in tools.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.split('\n')[0] if result.stdout else result.stderr.split('\n')[0]
                print(f"   ✅ {tool_name}: {version}")
            else:
                print(f"   ❌ {tool_name}: 未正确安装")
        except Exception:
            print(f"   ❌ {tool_name}: 未找到")

def create_directories():
    """创建必要目录"""
    print("📁 创建必要目录...")
    
    dirs = ['reports', 'logs', 'temp']
    for dir_name in dirs:
        try:
            os.makedirs(dir_name, exist_ok=True)
            print(f"   ✅ {dir_name}/")
        except Exception as e:
            print(f"   ❌ {dir_name}/: {e}")

def show_summary():
    """显示总结"""
    print("\n" + "=" * 60)
    print("📋 修复总结")
    print("=" * 60)
    
    print("\n✅ 已完成的修复:")
    print("1. 设置MySQL环境变量")
    print("2. 同步项目配置到数据库")
    print("3. 创建必要目录")
    print("4. 测试webhook功能")
    
    print("\n💡 如果仍有问题，请检查:")
    print("1. MySQL数据库连接是否正常")
    print("2. Git和Maven是否正确安装")
    print("3. Docker是否正常运行")
    print("4. Lark机器人webhook URL是否正确")
    print("5. 网络连接是否正常")
    
    print("\n🌐 访问地址:")
    print("   Web界面: http://localhost:8002/config")
    print("   API文档: http://localhost:8002/docs")
    print("   健康检查: http://localhost:8002/health")
    
    print("\n📝 日志查看:")
    print("   应用日志: tail -f logs/jacoco-api.log")
    print("   系统日志: journalctl -u jacoco-api -f")

def main():
    """主函数"""
    print("🔧 Linux环境快速修复工具")
    print("=" * 60)
    
    # 1. 设置环境变量
    setup_environment()
    
    # 2. 检查工具
    check_tools()
    
    # 3. 创建目录
    create_directories()
    
    # 4. 等待服务启动
    if not wait_for_service():
        print("❌ 服务未启动，请先启动服务:")
        print("   python3 app.py")
        return
    
    # 5. 同步配置
    sync_project_configs()
    
    # 6. 测试webhook
    test_webhook()
    
    # 7. 显示总结
    show_summary()

if __name__ == "__main__":
    main()
