"""
不同 Git 提供商的 webhook 验证工具。
此模块包含用于验证来自不同 Git 提供商的 webhook 请求的函数。
"""

import hmac
import hashlib
import logging
from typing import Optional, Dict, Any

from fastapi import Request, HTTPException, Header

from config import GIT_WEBHOOK_SECRET

logger = logging.getLogger(__name__)

class WebhookValidator:
    """webhook 验证器的基类。"""

    @staticmethod
    async def validate_webhook(
        request: Request,
        x_gitlab_token: Optional[str] = Header(None),
        x_hub_signature: Optional[str] = Header(None),
        x_hub_signature_256: Optional[str] = Header(None),
        x_gitee_token: Optional[str] = Header(None),
        x_gitee_event: Optional[str] = Header(None)
    ) -> bool:
        """
        根据提供商的签名方法验证 webhook 请求。

        参数:
            request: FastAPI 请求对象
            x_gitlab_token: GitLab webhook 令牌
            x_hub_signature: GitHub webhook 签名 (SHA1)
            x_hub_signature_256: GitHub webhook 签名 (SHA256)
            x_gitee_token: Gitee webhook 令牌
            x_gitee_event: Gitee 事件类型

        返回:
            如果验证成功则为 True，否则引发 HTTPException
        """
        # 获取原始请求体用于签名验证
        body = await request.body()

        # 检查是否配置了 webhook 密钥
        if not GIT_WEBHOOK_SECRET or GIT_WEBHOOK_SECRET == "your_default_secret_token":
            logger.warning("Webhook 密钥未正确配置！使用默认（不安全）值。")

        # 基于提供商头验证
        is_valid = False

        # 按顺序尝试每个验证器
        validators = [
            GitLabValidator(x_gitlab_token),
            GitHubValidator(x_hub_signature, x_hub_signature_256),
            GiteeValidator(x_gitee_token, x_gitee_event)
        ]

        for validator in validators:
            if validator.can_validate():
                is_valid = validator.validate(body)
                if is_valid:
                    break

        # 没有识别的认证头或验证失败
        if not is_valid:
            logger.warning("Webhook 验证失败或未找到可识别的认证头")
            raise HTTPException(
                status_code=401,
                detail="无效的 webhook 签名或令牌"
            )

        return True


class GitLabValidator:
    """GitLab webhooks 的验证器。"""

    def __init__(self, token: Optional[str]):
        self.token = token

    def can_validate(self) -> bool:
        """检查此验证器是否可用于当前请求。"""
        return self.token is not None

    def validate(self, body: bytes) -> bool:
        """使用令牌比较验证 GitLab webhook。"""
        logger.debug("正在验证 GitLab webhook")
        if self.token == GIT_WEBHOOK_SECRET:
            return True
        else:
            logger.warning("GitLab 令牌验证失败")
            return False


class GitHubValidator:
    """GitHub webhooks 的验证器。"""

    def __init__(self, signature: Optional[str], signature_256: Optional[str]):
        self.signature = signature
        self.signature_256 = signature_256

    def can_validate(self) -> bool:
        """检查此验证器是否可用于当前请求。"""
        return self.signature is not None or self.signature_256 is not None

    def validate(self, body: bytes) -> bool:
        """使用 HMAC 签名验证 GitHub webhook。"""
        logger.debug("正在验证 GitHub webhook")

        # 如果可用，首选 SHA256
        if self.signature_256:
            signature_parts = self.signature_256.split("=", 1)
            if len(signature_parts) == 2 and signature_parts[0] == "sha256":
                expected_signature = hmac.new(
                    GIT_WEBHOOK_SECRET.encode(),
                    body,
                    hashlib.sha256
                ).hexdigest()
                if hmac.compare_digest(signature_parts[1], expected_signature):
                    return True
                else:
                    logger.warning("GitHub SHA256 签名验证失败")

        # 如果 SHA256 不可用或验证失败，回退到 SHA1
        if self.signature:
            signature_parts = self.signature.split("=", 1)
            if len(signature_parts) == 2 and signature_parts[0] == "sha1":
                expected_signature = hmac.new(
                    GIT_WEBHOOK_SECRET.encode(),
                    body,
                    hashlib.sha1
                ).hexdigest()
                if hmac.compare_digest(signature_parts[1], expected_signature):
                    return True
                else:
                    logger.warning("GitHub SHA1 签名验证失败")

        return False


class GiteeValidator:
    """Gitee webhooks 的验证器。"""

    def __init__(self, token: Optional[str], event: Optional[str]):
        self.token = token
        self.event = event

    def can_validate(self) -> bool:
        """检查此验证器是否可用于当前请求。"""
        return self.token is not None

    def validate(self, body: bytes) -> bool:
        """使用令牌比较和事件类型验证 Gitee webhook。"""
        logger.debug("正在验证 Gitee webhook")
        if self.token == GIT_WEBHOOK_SECRET:
            # 检查这是否是推送事件
            if self.event and self.event.lower() == "push":
                return True
            else:
                logger.warning(f"不支持的 Gitee 事件类型: {self.event}")
        else:
            logger.warning("Gitee 令牌验证失败")

        return False
