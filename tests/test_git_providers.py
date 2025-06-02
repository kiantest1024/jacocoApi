"""
Git 提供商解析器的单元测试。
"""

from unittest.mock import patch

import pytest

from git_providers import GitProviderParser, GitLabParser, GitHubParser, GiteeParser


def test_gitlab_parser():
    """测试 GitLab 解析器。"""
    # 创建有效的 GitLab 负载
    payload = {
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
    
    # 测试解析
    provider_name, repo_url, commit_id, branch_name = GitLabParser.parse_payload(payload)
    assert provider_name == "gitlab"
    assert repo_url == "git@gitlab.com:test/repo.git"
    assert commit_id == "abcdef1234567890"
    assert branch_name == "main"
    
    # 测试无 SSH URL
    payload["project"]["git_ssh_url"] = None
    provider_name, repo_url, commit_id, branch_name = GitLabParser.parse_payload(payload)
    assert repo_url == "https://gitlab.com/test/repo.git"
    
    # 测试无效的 ref
    payload["ref"] = "refs/tags/v1.0"
    provider_name, repo_url, commit_id, branch_name = GitLabParser.parse_payload(payload)
    assert branch_name is None
    
    # 测试无效的负载
    invalid_payload = {"foo": "bar"}
    provider_name, repo_url, commit_id, branch_name = GitLabParser.parse_payload(invalid_payload)
    assert provider_name is None
    assert repo_url is None
    assert commit_id is None
    assert branch_name is None


def test_github_parser():
    """测试 GitHub 解析器。"""
    # 创建有效的 GitHub 负载
    payload = {
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
    
    # 测试解析
    provider_name, repo_url, commit_id, branch_name = GitHubParser.parse_payload(payload)
    assert provider_name == "github"
    assert repo_url == "git@github.com:test/repo.git"
    assert commit_id == "abcdef1234567890"
    assert branch_name == "main"
    
    # 测试无 SSH URL
    payload["repository"]["ssh_url"] = None
    provider_name, repo_url, commit_id, branch_name = GitHubParser.parse_payload(payload)
    assert repo_url == "https://github.com/test/repo.git"
    
    # 测试分支删除事件
    payload["deleted"] = True
    provider_name, repo_url, commit_id, branch_name = GitHubParser.parse_payload(payload)
    assert provider_name == "github"
    assert repo_url is None
    assert commit_id is None
    assert branch_name is None
    
    # 测试无效的 ref
    payload["deleted"] = False
    payload["ref"] = "refs/tags/v1.0"
    provider_name, repo_url, commit_id, branch_name = GitHubParser.parse_payload(payload)
    assert branch_name is None
    
    # 测试无效的负载
    invalid_payload = {"foo": "bar"}
    provider_name, repo_url, commit_id, branch_name = GitHubParser.parse_payload(invalid_payload)
    assert provider_name is None
    assert repo_url is None
    assert commit_id is None
    assert branch_name is None


def test_gitee_parser():
    """测试 Gitee 解析器。"""
    # 创建有效的 Gitee 负载
    payload = {
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
    
    # 测试解析
    provider_name, repo_url, commit_id, branch_name = GiteeParser.parse_payload(payload)
    assert provider_name == "gitee"
    assert repo_url == "git@gitee.com:test/repo.git"
    assert commit_id == "abcdef1234567890"
    assert branch_name == "main"
    
    # 测试无 SSH URL
    payload["repository"]["ssh_url"] = None
    provider_name, repo_url, commit_id, branch_name = GiteeParser.parse_payload(payload)
    assert repo_url == "https://gitee.com/test/repo"
    
    # 测试无效的 ref
    payload["ref"] = "refs/tags/v1.0"
    provider_name, repo_url, commit_id, branch_name = GiteeParser.parse_payload(payload)
    assert branch_name is None
    
    # 测试无效的负载
    invalid_payload = {"foo": "bar"}
    provider_name, repo_url, commit_id, branch_name = GiteeParser.parse_payload(invalid_payload)
    assert provider_name is None
    assert repo_url is None
    assert commit_id is None
    assert branch_name is None


def test_git_provider_parser():
    """测试 Git 提供商解析器。"""
    # 创建有效的 GitLab 负载
    gitlab_payload = {
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
    
    # 创建有效的 GitHub 负载
    github_payload = {
        "ref": "refs/heads/main",
        "after": "abcdef1234567890",
        "repository": {
            "clone_url": "https://github.com/test/repo.git",
            "ssh_url": "git@github.com:test/repo.git",
        }
    }
    
    # 创建有效的 Gitee 负载
    gitee_payload = {
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
    
    # 测试 GitLab 解析
    provider_name, repo_url, commit_id, branch_name = GitProviderParser.parse_payload(gitlab_payload)
    assert provider_name == "gitlab"
    
    # 测试 GitHub 解析
    provider_name, repo_url, commit_id, branch_name = GitProviderParser.parse_payload(github_payload)
    assert provider_name == "github"
    
    # 测试 Gitee 解析
    provider_name, repo_url, commit_id, branch_name = GitProviderParser.parse_payload(gitee_payload)
    assert provider_name == "gitee"
    
    # 测试未知提供商
    with patch('git_providers.logger.warning') as mock_warning:
        provider_name, repo_url, commit_id, branch_name = GitProviderParser.parse_payload({"foo": "bar"})
        assert provider_name is None
        assert repo_url is None
        assert commit_id is None
        assert branch_name is None
        mock_warning.assert_called_once()
