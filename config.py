from typing import Dict, Any

LARK_CONFIG: Dict[str, Any] = {
    "webhook_url": "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe",
    "enable_notifications": True,
    "timeout": 10,
    "retry_count": 3,
}

DEFAULT_SCAN_CONFIG: Dict[str, Any] = {
    "maven_goals": ["clean", "test", "jacoco:report"],
    "use_docker": True,
    "force_local_scan": False,
    "scan_timeout": 1800,
}

def get_service_config(repo_url: str) -> Dict[str, Any]:
    project_name = repo_url.replace('.git', '').split('/')[-1] if repo_url else "unknown"

    config = DEFAULT_SCAN_CONFIG.copy()
    config.update({
        "service_name": project_name,
        "repo_url": repo_url,
        "notification_webhook": LARK_CONFIG["webhook_url"],
    })
    return config
