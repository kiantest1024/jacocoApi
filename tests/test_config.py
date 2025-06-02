"""
配置模块的单元测试。
"""

from unittest.mock import patch

import pytest

from config import settings, get_service_config, SERVICE_CONFIG


def test_settings():
    """测试设置。"""
    # 测试默认值
    assert settings.API_TITLE == "JaCoCo Scan Trigger API"
    assert settings.API_VERSION == "1.0.0"
    assert isinstance(settings.ALLOWED_ORIGINS, list)
    assert settings.REDIS_HOST == "localhost"
    assert settings.REDIS_PORT == 6379
    
    # 测试 REDIS_URL 属性
    assert "redis://localhost:6379/0" in settings.REDIS_URL
    
    # 测试带密码的 REDIS_URL
    with patch.object(settings, 'REDIS_PASSWORD', "password"):
        assert "redis://:password@localhost:6379/0" in settings.REDIS_URL
    
    # 测试 Celery URL 方法
    with patch.object(settings, 'CELERY_BROKER_URL', ""):
        assert settings.get_celery_broker_url() == settings.REDIS_URL
    
    with patch.object(settings, 'CELERY_BROKER_URL', "redis://other-host:6379/0"):
        assert settings.get_celery_broker_url() == "redis://other-host:6379/0"
    
    with patch.object(settings, 'CELERY_RESULT_BACKEND', ""):
        assert settings.get_celery_result_backend() == settings.REDIS_URL
    
    with patch.object(settings, 'CELERY_RESULT_BACKEND', "redis://other-host:6379/0"):
        assert settings.get_celery_result_backend() == "redis://other-host:6379/0"


def test_service_config():
    """测试服务配置。"""
    # 测试直接查找
    with patch('config.SERVICE_CONFIG', {
        "git@example.com:user/repo.git": {"service_name": "test-service"}
    }):
        config = get_service_config("git@example.com:user/repo.git")
        assert config is not None
        assert config["service_name"] == "test-service"
    
    # 测试 SSH 到 HTTP 转换
    with patch('config.SERVICE_CONFIG', {
        "https://example.com/user/repo.git": {"service_name": "test-service"}
    }):
        config = get_service_config("git@example.com:user/repo.git")
        assert config is not None
        assert config["service_name"] == "test-service"
    
    # 测试 HTTP 到 SSH 转换
    with patch('config.SERVICE_CONFIG', {
        "git@example.com:user/repo.git": {"service_name": "test-service"}
    }):
        config = get_service_config("https://example.com/user/repo.git")
        assert config is not None
        assert config["service_name"] == "test-service"
    
    # 测试未找到
    with patch('config.SERVICE_CONFIG', {}):
        config = get_service_config("git@example.com:user/repo.git")
        assert config is None
