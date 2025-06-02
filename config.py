import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
from pydantic_settings import BaseSettings

# 如果存在 .env 文件，则从中加载环境变量
load_dotenv()

class Settings(BaseSettings):
    """从环境变量加载的应用程序设置，带有默认值。"""

    # API 设置
    API_TITLE: str = "JaCoCo Scan Trigger API"
    API_DESCRIPTION: str = "用于从 Git webhooks 触发 JaCoCo 代码覆盖率扫描的 API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # 安全设置
    GIT_WEBHOOK_SECRET: str = os.getenv("GIT_WEBHOOK_SECRET", "your_default_secret_token")
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")

    # 速率限制
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() in ("true", "1", "t")
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "3600"))

    # Celery 的 Redis 配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")

    @property
    def REDIS_URL(self) -> str:
        """从组件构造 Redis URL。"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Celery 配置
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "")

    def get_celery_broker_url(self) -> str:
        """获取 Celery 代理 URL，如果未设置则回退到 Redis URL。"""
        return self.CELERY_BROKER_URL or self.REDIS_URL

    def get_celery_result_backend(self) -> str:
        """获取 Celery 结果后端 URL，如果未设置则回退到 Redis URL。"""
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    # 日志设置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    class Config:
        """Pydantic 配置。"""
        env_file = ".env"
        case_sensitive = True

# 创建设置实例
settings = Settings()

# 为了向后兼容
GIT_WEBHOOK_SECRET = settings.GIT_WEBHOOK_SECRET
CELERY_BROKER_URL = settings.get_celery_broker_url()
CELERY_RESULT_BACKEND = settings.get_celery_result_backend()

# 服务配置映射
# 将仓库 URL 映射到特定服务的配置
SERVICE_CONFIG: Dict[str, Dict[str, Any]] = {
    "git@your-git-server.com:user/service-a.git": {
        "service_name": "service-a",
        "scan_method": "solution1",
        "notification_webhook": "https://open.larksuite.com/open-apis/bot/v2/hook/08ce42ce-4136-476d-8aef-8517e0f5a616",
        # ... 其他特定于服务的配置
    },
    "https://your-git-server.com/user/service-b.git": {
        "service_name": "service-b",
        "scan_method": "solution2",
        "notification_webhook": "https://open.larksuite.com/open-apis/bot/v2/hook/08ce42ce-4136-476d-8aef-8517e0f5a616",
        "coverage_settings_path": "/path/to/your/coverage-settings.xml",
        # ... 其他特定于服务的配置
    },
    # Java Login System 项目配置 (Docker 扫描)
    "https://github.com/your-username/java-login-system.git": {
        "service_name": "java-login-system",
        "scan_method": "jacoco",
        "project_type": "maven",
        "docker_image": "jacoco-scanner:latest",
        "notification_webhook": "https://open.larksuite.com/open-apis/bot/v2/hook/08ce42ce-4136-476d-8aef-8517e0f5a616",
        "coverage_threshold": 50.0,
        "maven_goals": ["clean", "test", "jacoco:report"],
        "report_formats": ["xml", "html"],
        "use_docker": True,
        # ... 其他特定于服务的配置
    },
    # 本地开发配置示例 (Docker 扫描)
    "file:///d:/Personal/Script/GE/java-login-system": {
        "service_name": "java-login-system-local",
        "scan_method": "jacoco",
        "project_type": "maven",
        "docker_image": "jacoco-scanner:latest",
        "notification_webhook": "https://open.larksuite.com/open-apis/bot/v2/hook/08ce42ce-4136-476d-8aef-8517e0f5a616",
        "coverage_threshold": 50.0,
        "maven_goals": ["clean", "test", "jacoco:report"],
        "report_formats": ["xml", "html"],
        "use_docker": True,
    },
    # 测试用的本地仓库配置
    "https://github.com/test/java-login-system.git": {
        "service_name": "java-login-system-test",
        "scan_method": "jacoco",
        "project_type": "maven",
        "docker_image": "jacoco-scanner:latest",
        "notification_webhook": "https://open.larksuite.com/open-apis/bot/v2/hook/08ce42ce-4136-476d-8aef-8517e0f5a616",
        "coverage_threshold": 30.0,
        "maven_goals": ["clean", "test", "jacoco:report"],
        "report_formats": ["xml", "html"],
        "use_docker": True,
    }
    # 根据需要添加更多仓库配置
}

# 通过仓库 URL 获取服务配置的函数
def get_service_config(repo_url: str) -> Optional[Dict[str, Any]]:
    """
    通过仓库 URL 获取服务配置。
    如果需要，处理不同的 URL 格式（HTTP 与 SSH）。

    参数:
        repo_url: 仓库 URL（SSH 或 HTTP）

    返回:
        服务配置字典，如果未找到则返回 None
    """
    # 直接查找
    if repo_url in SERVICE_CONFIG:
        return SERVICE_CONFIG[repo_url]

    # 尝试规范化 URL 以进行查找（处理 HTTP 与 SSH 变体）
    # 这是一个简单的示例 - 您可能需要更复杂的匹配逻辑
    normalized_url = repo_url
    if repo_url.startswith("git@"):
        # 将 SSH URL 转换为 HTTP 格式以进行匹配
        parts = repo_url.split(":")
        if len(parts) == 2:
            domain = parts[0].replace("git@", "")
            path = parts[1]
            normalized_url = f"https://{domain}/{path}"
    elif repo_url.startswith("https://"):
        # 将 HTTP URL 转换为 SSH 格式以进行匹配
        parts = repo_url.replace("https://", "").split("/", 1)
        if len(parts) == 2:
            domain = parts[0]
            path = parts[1]
            normalized_url = f"git@{domain}:{path}"

    # 使用规范化的 URL 尝试查找
    return SERVICE_CONFIG.get(normalized_url)
