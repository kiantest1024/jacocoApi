"""
Git 提供商负载解析器，用于处理 webhook。
此模块包含用于解析来自不同 Git 提供商的 webhook 负载的函数。
"""

import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class GitProviderParser:
    """Git 提供商负载解析器的基类。"""

    @staticmethod
    def parse_payload(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        解析 webhook 负载以提取仓库信息。

        参数:
            payload: 作为字典的 webhook 负载

        返回:
            包含 (provider_name, repo_url, commit_id, branch_name) 的元组
            如果无法提取，这些值中的任何一个都可能为 None
        """
        # 按顺序尝试每个提供商解析器
        for parser in [GitLabParser, GitHubParser, GiteeParser]:
            result = parser.parse_payload(payload)
            if result[0]:  # 如果 provider_name 不是 None，我们有匹配
                return result

        # 没有解析器匹配
        logger.warning(f"未知的 Git 提供商负载格式。可用键: {list(payload.keys())}")
        return None, None, None, None


class GitLabParser:
    """GitLab webhook 负载的解析器。"""

    @staticmethod
    def parse_payload(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """解析 GitLab webhook 负载。"""
        # 检查这是否是 GitLab 负载
        if not ('project' in payload and 'commits' in payload and len(payload['commits']) > 0):
            return None, None, None, None

        logger.info("检测到 GitLab webhook 负载")

        # 提取仓库 URL（如果可用，首选 SSH URL）
        repo_url = payload['project'].get('git_ssh_url') or payload['project'].get('git_http_url')

        # 提取提交 ID（最新提交）
        commit_id = payload['commits'][0].get('id')

        # 从 ref 中提取分支名称
        branch_name = None
        ref = payload.get('ref')  # 格式: refs/heads/branch-name
        if ref and ref.startswith('refs/heads/'):
            branch_name = ref.split('/')[-1]

        return "gitlab", repo_url, commit_id, branch_name


class GitHubParser:
    """GitHub webhook 负载的解析器。"""

    @staticmethod
    def parse_payload(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """解析 GitHub webhook 负载。"""
        # 检查这是否是 GitHub 负载
        if not ('repository' in payload and 'after' in payload and 'ref' in payload):
            return None, None, None, None

        # 检查这是否是分支删除事件（我们应该忽略这些）
        if payload.get('deleted'):
            logger.info(f"忽略 GitHub 分支删除事件")
            return "github", None, None, None

        logger.info("检测到 GitHub webhook 负载")

        # 提取仓库 URL（如果可用，首选 SSH URL）
        repo_url = payload['repository'].get('ssh_url') or payload['repository'].get('clone_url')

        # 提取提交 ID
        commit_id = payload.get('after')  # 推送后的新提交 ID

        # 从 ref 中提取分支名称
        branch_name = None
        ref = payload.get('ref')  # 格式: refs/heads/branch-name
        if ref and ref.startswith('refs/heads/'):
            branch_name = ref.split('/')[-1]

        return "github", repo_url, commit_id, branch_name


class GiteeParser:
    """Gitee webhook 负载的解析器。"""

    @staticmethod
    def parse_payload(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """解析 Gitee webhook 负载。"""
        # 检查这是否是 Gitee 负载
        if not ('repository' in payload and 'head_commit' in payload and 'ref' in payload):
            return None, None, None, None

        logger.info("检测到 Gitee webhook 负载")

        # 提取仓库 URL（如果可用，首选 SSH URL）
        repo_url = payload['repository'].get('ssh_url') or payload['repository'].get('web_url')

        # 提取提交 ID
        commit_id = payload['head_commit'].get('id')

        # 从 ref 中提取分支名称
        branch_name = None
        ref = payload.get('ref')  # 格式: refs/heads/branch-name
        if ref and ref.startswith('refs/heads/'):
            branch_name = ref.split('/')[-1]

        return "gitee", repo_url, commit_id, branch_name
