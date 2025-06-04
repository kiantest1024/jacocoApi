#!/usr/bin/env python3
"""
配置管理模块
"""

from typing import Dict, Any, List

# 默认扫描配置
DEFAULT_SCAN_CONFIG: Dict[str, Any] = {
    "scan_method": "jacoco",
    "project_type": "maven",
    "docker_image": "jacoco-scanner:latest",
    "notification_webhook": "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe",
    "coverage_threshold": 50.0,
    "maven_goals": ["clean", "test", "jacoco:report"],
    "report_formats": ["xml", "html", "json"],
    "use_docker": False,  # 使用本地扫描
    "use_shared_container": False,  # 禁用共享容器
    "force_local_scan": True,  # 强制本地扫描
    "sync_mode": True,  # 同步模式
    "scan_timeout": 1800,
    "max_retries": 3,
}

# 自定义项目配置
CUSTOM_PROJECT_CONFIG: Dict[str, Dict[str, Any]] = {}

def get_project_name_from_url(repo_url: str) -> str:
    url = repo_url.replace('.git', '')
    if '/' in url:
        return url.split('/')[-1]
    return url

def get_service_config(repo_url: str, project_name: str = None) -> Dict[str, Any]:
    if not project_name:
        project_name = get_project_name_from_url(repo_url)
    
    config = DEFAULT_SCAN_CONFIG.copy()
    config.update({
        "service_name": project_name,
        "repo_url": repo_url,
        "local_repo_path": f"./repos/{project_name}",
    })
    
    if project_name in CUSTOM_PROJECT_CONFIG:
        config.update(CUSTOM_PROJECT_CONFIG[project_name])
    
    return config

def is_supported_project_type(_: str) -> bool:
    return True

def get_available_repos() -> List[str]:
    return [
        "任何配置了 webhook 的 Maven 项目",
        "支持 GitHub 和 GitLab",
        "自动检测项目类型",
        "通用 JaCoCo 扫描服务"
    ]
