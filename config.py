import os
from typing import Dict, Any, List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_TITLE: str = "Universal JaCoCo Scanner API"
    API_DESCRIPTION: str = "Universal JaCoCo coverage scanner for any Maven project"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    GIT_WEBHOOK_SECRET: str = os.getenv("GIT_WEBHOOK_SECRET", "your_default_secret_token")

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() in ("true", "1", "t")
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "3600"))

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SCAN_TIMEOUT: int = int(os.getenv("SCAN_TIMEOUT", "1800"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
GIT_WEBHOOK_SECRET = settings.GIT_WEBHOOK_SECRET
CELERY_BROKER_URL = settings.REDIS_URL
CELERY_RESULT_BACKEND = settings.REDIS_URL

# Lark通知配置
LARK_CONFIG: Dict[str, Any] = {
    "webhook_url": os.getenv("LARK_WEBHOOK_URL", "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe"),
    "enable_notifications": os.getenv("LARK_ENABLE_NOTIFICATIONS", "true").lower() in ("true", "1", "yes"),
    "timeout": int(os.getenv("LARK_TIMEOUT", "10")),
    "retry_count": int(os.getenv("LARK_RETRY_COUNT", "3")),
    "retry_delay": int(os.getenv("LARK_RETRY_DELAY", "1")),
}

DEFAULT_SCAN_CONFIG: Dict[str, Any] = {
    "scan_method": "docker",  # 优先使用Docker扫描
    "project_type": "maven",
    "docker_image": "jacoco-scanner:latest",
    "notification_webhook": LARK_CONFIG["webhook_url"],  # 从Lark配置中读取
    "coverage_threshold": 50.0,
    "maven_goals": ["clean", "test", "jacoco:report"],
    "report_formats": ["xml", "html", "json"],
    "use_docker": True,  # 启用Docker扫描
    "use_shared_container": True,  # 启用共享容器模式  # 启用Docker（优先）
    "force_local_scan": False,  # 不强制本地扫描
    "sync_mode": True,  # 启用同步模式用于调试
    "use_incremental_update": True,
    "scan_timeout": 1800,
    "max_retries": 3,
}

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
