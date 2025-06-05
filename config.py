from typing import Dict, Any

DEFAULT_SCAN_CONFIG: Dict[str, Any] = {
    "scan_method": "jacoco",
    "project_type": "maven",
    "notification_webhook": "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe",
    "maven_goals": ["clean", "test", "jacoco:report"],
    "use_docker": False,
    "force_local_scan": True,
    "sync_mode": True,
    "scan_timeout": 1800,
}

# Lark通知配置
LARK_CONFIG: Dict[str, Any] = {
    "webhook_url": "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe",
    "enable_notifications": True,
    "timeout": 10,
    "retry_count": 3,
    "retry_delay": 1,
}

def get_project_name_from_url(repo_url: str) -> str:
    url = repo_url.replace('.git', '')
    return url.split('/')[-1] if '/' in url else url

def get_service_config(repo_url: str, project_name: str = None) -> Dict[str, Any]:
    if not project_name:
        project_name = get_project_name_from_url(repo_url)

    config = DEFAULT_SCAN_CONFIG.copy()
    config.update({
        "service_name": project_name,
        "repo_url": repo_url,
        "local_repo_path": f"./repos/{project_name}",
    })
    return config
