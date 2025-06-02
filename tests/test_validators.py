"""
Webhook 验证器的单元测试。
"""

import hmac
import hashlib
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi import HTTPException

from validators import WebhookValidator, GitLabValidator, GitHubValidator, GiteeValidator
from config import GIT_WEBHOOK_SECRET


def test_gitlab_validator():
    """测试 GitLab 验证器。"""
    # 创建验证器
    validator = GitLabValidator("correct_token")
    
    # 测试 can_validate
    assert validator.can_validate() is True
    
    # 测试 validate
    with patch('validators.GIT_WEBHOOK_SECRET', "correct_token"):
        assert validator.validate(b"payload") is True
    
    # 测试无效令牌
    with patch('validators.GIT_WEBHOOK_SECRET', "correct_token"):
        validator = GitLabValidator("wrong_token")
        assert validator.validate(b"payload") is False
    
    # 测试 None 令牌
    validator = GitLabValidator(None)
    assert validator.can_validate() is False


def test_github_validator():
    """测试 GitHub 验证器。"""
    # 创建有效的 SHA256 签名
    payload = b"payload"
    secret = "secret"
    signature_256 = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # 创建有效的 SHA1 签名
    signature_1 = "sha1=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha1
    ).hexdigest()
    
    # 测试 SHA256 验证
    with patch('validators.GIT_WEBHOOK_SECRET', secret):
        validator = GitHubValidator(None, signature_256)
        assert validator.can_validate() is True
        assert validator.validate(payload) is True
    
    # 测试 SHA1 验证
    with patch('validators.GIT_WEBHOOK_SECRET', secret):
        validator = GitHubValidator(signature_1, None)
        assert validator.can_validate() is True
        assert validator.validate(payload) is True
    
    # 测试无效签名
    with patch('validators.GIT_WEBHOOK_SECRET', secret):
        validator = GitHubValidator("sha1=invalid", None)
        assert validator.validate(payload) is False
        
        validator = GitHubValidator(None, "sha256=invalid")
        assert validator.validate(payload) is False
    
    # 测试 None 签名
    validator = GitHubValidator(None, None)
    assert validator.can_validate() is False


def test_gitee_validator():
    """测试 Gitee 验证器。"""
    # 创建验证器
    validator = GiteeValidator("correct_token", "Push")
    
    # 测试 can_validate
    assert validator.can_validate() is True
    
    # 测试 validate
    with patch('validators.GIT_WEBHOOK_SECRET', "correct_token"):
        assert validator.validate(b"payload") is True
    
    # 测试无效令牌
    with patch('validators.GIT_WEBHOOK_SECRET', "correct_token"):
        validator = GiteeValidator("wrong_token", "Push")
        assert validator.validate(b"payload") is False
    
    # 测试无效事件
    with patch('validators.GIT_WEBHOOK_SECRET', "correct_token"):
        validator = GiteeValidator("correct_token", "Issue")
        assert validator.validate(b"payload") is False
    
    # 测试 None 令牌
    validator = GiteeValidator(None, "Push")
    assert validator.can_validate() is False


@pytest.mark.asyncio
async def test_webhook_validator():
    """测试 Webhook 验证器。"""
    # 创建模拟请求
    mock_request = AsyncMock()
    mock_request.body.return_value = b"payload"
    
    # 测试 GitLab 验证
    with patch('validators.GitLabValidator.validate', return_value=True):
        result = await WebhookValidator.validate_webhook(
            mock_request,
            x_gitlab_token="token",
            x_hub_signature=None,
            x_hub_signature_256=None,
            x_gitee_token=None,
            x_gitee_event=None
        )
        assert result is True
    
    # 测试 GitHub 验证
    with patch('validators.GitHubValidator.validate', return_value=True):
        result = await WebhookValidator.validate_webhook(
            mock_request,
            x_gitlab_token=None,
            x_hub_signature="signature",
            x_hub_signature_256=None,
            x_gitee_token=None,
            x_gitee_event=None
        )
        assert result is True
    
    # 测试 Gitee 验证
    with patch('validators.GiteeValidator.validate', return_value=True):
        result = await WebhookValidator.validate_webhook(
            mock_request,
            x_gitlab_token=None,
            x_hub_signature=None,
            x_hub_signature_256=None,
            x_gitee_token="token",
            x_gitee_event="Push"
        )
        assert result is True
    
    # 测试验证失败
    with patch('validators.GitLabValidator.validate', return_value=False), \
         patch('validators.GitHubValidator.validate', return_value=False), \
         patch('validators.GiteeValidator.validate', return_value=False):
        with pytest.raises(HTTPException) as excinfo:
            await WebhookValidator.validate_webhook(
                mock_request,
                x_gitlab_token="token",
                x_hub_signature=None,
                x_hub_signature_256=None,
                x_gitee_token=None,
                x_gitee_event=None
            )
        assert excinfo.value.status_code == 401
        assert "Invalid webhook signature or token" in excinfo.value.detail
    
    # 测试无认证头
    with pytest.raises(HTTPException) as excinfo:
        await WebhookValidator.validate_webhook(
            mock_request,
            x_gitlab_token=None,
            x_hub_signature=None,
            x_hub_signature_256=None,
            x_gitee_token=None,
            x_gitee_event=None
        )
    assert excinfo.value.status_code == 401
