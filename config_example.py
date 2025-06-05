# 多项目多机器人配置示例
# 复制此文件为 config.py 并根据实际情况修改

from typing import Dict, Any
import re

# Lark机器人配置 - 支持多个机器人
LARK_BOTS: Dict[str, Dict[str, Any]] = {
    "default": {
        "webhook_url": "https://open.larksuite.com/open-apis/bot/v2/hook/your-default-webhook-id",
        "name": "默认机器人",
        "timeout": 10,
        "retry_count": 3,
    },
    "team_frontend": {
        "webhook_url": "https://open.larksuite.com/open-apis/bot/v2/hook/frontend-team-webhook-id",
        "name": "前端团队机器人",
        "timeout": 10,
        "retry_count": 3,
    },
    "team_backend": {
        "webhook_url": "https://open.larksuite.com/open-apis/bot/v2/hook/backend-team-webhook-id",
        "name": "后端团队机器人",
        "timeout": 10,
        "retry_count": 3,
    },
    "team_devops": {
        "webhook_url": "https://open.larksuite.com/open-apis/bot/v2/hook/devops-team-webhook-id",
        "name": "DevOps团队机器人",
        "timeout": 15,
        "retry_count": 5,
    },
}

# 项目与机器人映射配置
PROJECT_BOT_MAPPING: Dict[str, str] = {
    # 精确匹配项目名称
    "jacocotest": "default",
    "user-service": "team_backend",
    "order-service": "team_backend",
    "payment-service": "team_backend",
    "web-frontend": "team_frontend",
    "mobile-app": "team_frontend",
    "admin-dashboard": "team_frontend",
    "deployment-scripts": "team_devops",
    "monitoring-tools": "team_devops",
    
    # 通配符匹配 - 支持 * 通配符
    "frontend-*": "team_frontend",      # 所有以 frontend- 开头的项目
    "backend-*": "team_backend",        # 所有以 backend- 开头的项目
    "*-service": "team_backend",        # 所有以 -service 结尾的项目
    "*-web": "team_frontend",           # 所有以 -web 结尾的项目
    "devops-*": "team_devops",          # 所有以 devops- 开头的项目
    "*-deploy": "team_devops",          # 所有以 -deploy 结尾的项目
    
    # URL路径匹配 - 支持仓库URL中的路径匹配
    "*/frontend/*": "team_frontend",    # URL中包含 /frontend/ 的项目
    "*/backend/*": "team_backend",      # URL中包含 /backend/ 的项目
    "*/devops/*": "team_devops",        # URL中包含 /devops/ 的项目
    "*/team-a/*": "team_frontend",      # URL中包含 /team-a/ 的项目
    "*/team-b/*": "team_backend",       # URL中包含 /team-b/ 的项目
}

# 默认扫描配置
DEFAULT_SCAN_CONFIG: Dict[str, Any] = {
    "maven_goals": ["clean", "test", "jacoco:report"],
    "use_docker": True,
    "force_local_scan": False,
    "scan_timeout": 1800,
    "enable_notifications": True,
}

def get_bot_for_project(repo_url: str, project_name: str) -> str:
    """根据项目信息匹配对应的机器人ID"""
    
    # 1. 精确匹配项目名称
    if project_name in PROJECT_BOT_MAPPING:
        return PROJECT_BOT_MAPPING[project_name]
    
    # 2. 通配符匹配项目名称
    for pattern, bot_id in PROJECT_BOT_MAPPING.items():
        if '*' in pattern and '/' not in pattern:
            # 将通配符转换为正则表达式
            regex_pattern = pattern.replace('*', '.*')
            if re.match(f"^{regex_pattern}$", project_name):
                return bot_id
    
    # 3. URL路径匹配
    for pattern, bot_id in PROJECT_BOT_MAPPING.items():
        if '/' in pattern and '*' in pattern:
            regex_pattern = pattern.replace('*', '.*')
            if re.search(regex_pattern, repo_url):
                return bot_id
    
    # 4. 返回默认机器人
    return "default"

def get_lark_config(bot_id: str) -> Dict[str, Any]:
    """获取指定机器人的配置"""
    return LARK_BOTS.get(bot_id, LARK_BOTS["default"])

def get_service_config(repo_url: str) -> Dict[str, Any]:
    """获取项目的完整配置"""
    project_name = repo_url.replace('.git', '').split('/')[-1] if repo_url else "unknown"
    
    # 获取匹配的机器人ID
    bot_id = get_bot_for_project(repo_url, project_name)
    lark_config = get_lark_config(bot_id)
    
    config = DEFAULT_SCAN_CONFIG.copy()
    config.update({
        "service_name": project_name,
        "repo_url": repo_url,
        "bot_id": bot_id,
        "bot_name": lark_config["name"],
        "notification_webhook": lark_config["webhook_url"],
        "notification_timeout": lark_config["timeout"],
        "notification_retry_count": lark_config["retry_count"],
    })
    return config

def list_all_bots() -> Dict[str, Dict[str, Any]]:
    """列出所有配置的机器人"""
    return LARK_BOTS.copy()

def list_project_mappings() -> Dict[str, str]:
    """列出所有项目映射"""
    return PROJECT_BOT_MAPPING.copy()

# 配置验证函数
def validate_config() -> bool:
    """验证配置的有效性"""
    errors = []
    
    # 检查是否有默认机器人
    if "default" not in LARK_BOTS:
        errors.append("缺少 'default' 机器人配置")
    
    # 检查所有机器人配置
    for bot_id, bot_config in LARK_BOTS.items():
        if not bot_config.get("webhook_url"):
            errors.append(f"机器人 '{bot_id}' 缺少 webhook_url")
        if not bot_config.get("name"):
            errors.append(f"机器人 '{bot_id}' 缺少 name")
    
    # 检查映射中引用的机器人是否存在
    for pattern, bot_id in PROJECT_BOT_MAPPING.items():
        if bot_id not in LARK_BOTS:
            errors.append(f"映射 '{pattern}' 引用了不存在的机器人 '{bot_id}'")
    
    if errors:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("配置验证通过")
    return True

if __name__ == "__main__":
    # 运行配置验证
    validate_config()
    
    # 测试一些项目匹配
    test_projects = [
        ("http://git.example.com/frontend/web-app.git", "web-app"),
        ("http://git.example.com/backend/user-service.git", "user-service"),
        ("http://git.example.com/devops/deploy-scripts.git", "deploy-scripts"),
        ("http://git.example.com/team-a/frontend-dashboard.git", "frontend-dashboard"),
    ]
    
    print("\n项目匹配测试:")
    for repo_url, project_name in test_projects:
        bot_id = get_bot_for_project(repo_url, project_name)
        bot_config = get_lark_config(bot_id)
        print(f"  {project_name} -> {bot_config['name']} ({bot_id})")
