"""
Pytest 配置文件。
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from config import settings


@pytest.fixture
def test_client():
    """
    创建 FastAPI 测试客户端。
    """
    return TestClient(app)


@pytest.fixture
def mock_settings(monkeypatch):
    """
    模拟设置以进行测试。
    """
    # 设置测试环境变量
    monkeypatch.setattr(settings, 'GIT_WEBHOOK_SECRET', 'test_secret')
    monkeypatch.setattr(settings, 'DEBUG', True)
    return settings


@pytest.fixture
def mock_service_config():
    """
    模拟服务配置以进行测试。
    """
    return {
        "service_name": "test-service",
        "scan_method": "solution1",
        "notification_webhook": "http://test.webhook.url",
    }


@pytest.fixture
def mock_github_payload():
    """
    模拟 GitHub webhook 负载以进行测试。
    """
    return {
        "ref": "refs/heads/main",
        "after": "abcdef1234567890",
        "repository": {
            "clone_url": "https://github.com/test/repo.git",
            "ssh_url": "git@github.com:test/repo.git",
        },
        "commits": [
            {
                "id": "abcdef1234567890",
                "message": "Test commit",
            }
        ]
    }


@pytest.fixture
def mock_gitlab_payload():
    """
    模拟 GitLab webhook 负载以进行测试。
    """
    return {
        "ref": "refs/heads/main",
        "project": {
            "git_http_url": "https://gitlab.com/test/repo.git",
            "git_ssh_url": "git@gitlab.com:test/repo.git",
        },
        "commits": [
            {
                "id": "abcdef1234567890",
                "message": "Test commit",
            }
        ]
    }


@pytest.fixture
def mock_gitee_payload():
    """
    模拟 Gitee webhook 负载以进行测试。
    """
    return {
        "ref": "refs/heads/main",
        "repository": {
            "web_url": "https://gitee.com/test/repo",
            "ssh_url": "git@gitee.com:test/repo.git",
        },
        "head_commit": {
            "id": "abcdef1234567890",
            "message": "Test commit",
        }
    }
