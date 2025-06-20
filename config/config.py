from typing import Dict, Any, Optional
import re
import hashlib

# 管理员密码配置（用于修改已存在的配置）
ADMIN_PASSWORD_HASH = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # "password"的SHA256

# Lark机器人配置 - 支持多个机器人
LARK_BOTS: Dict[str, Dict[str, Any]] = {
    "default": {
        "webhook_url": "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe",
        "name": "默认机器人",
        "timeout": 10,
        "retry_count": 3,
        "is_custom": False,
    }
}

# 项目与机器人映射配置
PROJECT_BOT_MAPPING: Dict[str, str] = {
    # 项目名称或仓库URL模式 -> 机器人ID
    "jacocotest": "default",
    "project-a": "team_a",
    "project-b": "team_b",
    "frontend-*": "team_a",  # 支持通配符
    "backend-*": "team_b",
    "*/team-a/*": "team_a",  # 支持路径匹配
    "*/team-b/*": "team_b",
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

    # 文件配置系统（回退方案）
    # 1. 精确匹配项目名称
    if project_name in PROJECT_BOT_MAPPING:
        return PROJECT_BOT_MAPPING[project_name]

    # 2. 通配符匹配项目名称
    for pattern, bot_id in PROJECT_BOT_MAPPING.items():
        if '*' in pattern:
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

def verify_admin_password(password: str) -> bool:
    """验证管理员密码"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == ADMIN_PASSWORD_HASH

def add_custom_bot(bot_id: str, name: str, webhook_url: str) -> bool:
    """添加自定义机器人"""
    try:
        LARK_BOTS[bot_id] = {
            "webhook_url": webhook_url,
            "name": name,
            "timeout": 10,
            "retry_count": 3,
            "is_custom": True,
        }
        return True
    except Exception:
        return False

def remove_custom_bot(bot_id: str) -> bool:
    """删除自定义机器人（仅限自定义机器人）"""
    try:
        if bot_id in LARK_BOTS and LARK_BOTS[bot_id].get("is_custom", False):
            del LARK_BOTS[bot_id]
            return True
        return False
    except Exception:
        return False

def check_project_exists(project_name: str) -> Optional[Dict[str, Any]]:
    """检查项目是否已配置"""
    if project_name in PROJECT_BOT_MAPPING:
        bot_id = PROJECT_BOT_MAPPING[project_name]
        bot_config = get_lark_config(bot_id)
        return {
            "exists": True,
            "project_name": project_name,
            "bot_id": bot_id,
            "bot_name": bot_config["name"],
            "webhook_url": bot_config["webhook_url"]
        }
    return {"exists": False}

def batch_add_projects(projects: list, default_bot_id: str = "default") -> Dict[str, Any]:
    """批量添加项目"""
    results = {
        "success": [],
        "failed": [],
        "existing": [],
        "total": len(projects)
    }

    for project_data in projects:
        project_name = project_data.get("name", "").strip()
        git_url = project_data.get("git_url", "").strip()
        bot_id = project_data.get("bot_id", default_bot_id)

        if not project_name:
            results["failed"].append({
                "project": project_data,
                "reason": "项目名称为空"
            })
            continue

        # 检查是否已存在
        existing_check = check_project_exists(project_name)
        if existing_check["exists"]:
            results["existing"].append({
                "project_name": project_name,
                "current_bot": existing_check["bot_name"],
                "current_url": existing_check["webhook_url"]
            })
            continue

        # 添加新项目
        try:
            PROJECT_BOT_MAPPING[project_name] = bot_id
            results["success"].append({
                "project_name": project_name,
                "git_url": git_url,
                "bot_id": bot_id
            })
        except Exception as e:
            results["failed"].append({
                "project": project_data,
                "reason": str(e)
            })

    return results
