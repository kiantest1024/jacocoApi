"""
API 端点的单元测试。
"""

import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock

import pytest
from fastapi import status

from config import get_service_config


def test_health_check(test_client):
    """测试健康检查端点。"""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_docs_endpoint(test_client):
    """测试文档端点。"""
    response = test_client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_endpoint(test_client):
    """测试 OpenAPI 端点。"""
    response = test_client.get("/openapi.json")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    schema = response.json()
    assert "paths" in schema
    assert "/health" in schema["paths"]
    assert "/scan-trigger" in schema["paths"]


@patch('main.get_service_config')
@patch('main.celery_app')
def test_webhook_github(mock_celery, mock_get_service_config, test_client, mock_github_payload, mock_service_config, mock_settings):
    """测试 GitHub webhook 端点。"""
    # 模拟服务配置查找
    mock_get_service_config.return_value = mock_service_config
    
    # 模拟 Celery 任务
    mock_task = MagicMock()
    mock_task.id = "test-task-id"
    mock_celery.send_task.return_value = mock_task
    
    # 准备请求
    payload = json.dumps(mock_github_payload).encode()
    signature = hmac.new(
        mock_settings.GIT_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # 发送请求
    response = test_client.post(
        "/scan-trigger",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={signature}"
        }
    )
    
    # 验证响应
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["task_id"] == "test-task-id"
    
    # 验证服务配置查找
    mock_get_service_config.assert_called_once_with(mock_github_payload["repository"]["ssh_url"])
    
    # 验证 Celery 任务
    mock_celery.send_task.assert_called_once()
    args, kwargs = mock_celery.send_task.call_args
    assert args[0] == 'scan_tasks.execute_scan'
    assert args[1][0] == mock_github_payload["repository"]["ssh_url"]  # repo_url
    assert args[1][1] == mock_github_payload["after"]  # commit_id
    assert args[1][2] == "main"  # branch_name
    assert args[1][3] == mock_service_config  # service_config


@patch('main.get_service_config')
@patch('main.celery_app')
def test_webhook_gitlab(mock_celery, mock_get_service_config, test_client, mock_gitlab_payload, mock_service_config, mock_settings):
    """测试 GitLab webhook 端点。"""
    # 模拟服务配置查找
    mock_get_service_config.return_value = mock_service_config
    
    # 模拟 Celery 任务
    mock_task = MagicMock()
    mock_task.id = "test-task-id"
    mock_celery.send_task.return_value = mock_task
    
    # 发送请求
    response = test_client.post(
        "/scan-trigger",
        json=mock_gitlab_payload,
        headers={
            "X-Gitlab-Token": mock_settings.GIT_WEBHOOK_SECRET
        }
    )
    
    # 验证响应
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["task_id"] == "test-task-id"
    
    # 验证服务配置查找
    mock_get_service_config.assert_called_once_with(mock_gitlab_payload["project"]["git_ssh_url"])
    
    # 验证 Celery 任务
    mock_celery.send_task.assert_called_once()
    args, kwargs = mock_celery.send_task.call_args
    assert args[0] == 'scan_tasks.execute_scan'
    assert args[1][0] == mock_gitlab_payload["project"]["git_ssh_url"]  # repo_url
    assert args[1][1] == mock_gitlab_payload["commits"][0]["id"]  # commit_id
    assert args[1][2] == "main"  # branch_name
    assert args[1][3] == mock_service_config  # service_config


@patch('main.get_service_config')
@patch('main.celery_app')
def test_webhook_gitee(mock_celery, mock_get_service_config, test_client, mock_gitee_payload, mock_service_config, mock_settings):
    """测试 Gitee webhook 端点。"""
    # 模拟服务配置查找
    mock_get_service_config.return_value = mock_service_config
    
    # 模拟 Celery 任务
    mock_task = MagicMock()
    mock_task.id = "test-task-id"
    mock_celery.send_task.return_value = mock_task
    
    # 发送请求
    response = test_client.post(
        "/scan-trigger",
        json=mock_gitee_payload,
        headers={
            "X-Gitee-Token": mock_settings.GIT_WEBHOOK_SECRET,
            "X-Gitee-Event": "Push"
        }
    )
    
    # 验证响应
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["task_id"] == "test-task-id"
    
    # 验证服务配置查找
    mock_get_service_config.assert_called_once_with(mock_gitee_payload["repository"]["ssh_url"])
    
    # 验证 Celery 任务
    mock_celery.send_task.assert_called_once()
    args, kwargs = mock_celery.send_task.call_args
    assert args[0] == 'scan_tasks.execute_scan'
    assert args[1][0] == mock_gitee_payload["repository"]["ssh_url"]  # repo_url
    assert args[1][1] == mock_gitee_payload["head_commit"]["id"]  # commit_id
    assert args[1][2] == "main"  # branch_name
    assert args[1][3] == mock_service_config  # service_config


@patch('main.get_service_config')
def test_webhook_no_service_config(mock_get_service_config, test_client, mock_github_payload, mock_settings):
    """测试没有服务配置的情况。"""
    # 模拟服务配置查找
    mock_get_service_config.return_value = None
    
    # 准备请求
    payload = json.dumps(mock_github_payload).encode()
    signature = hmac.new(
        mock_settings.GIT_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # 发送请求
    response = test_client.post(
        "/scan-trigger",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={signature}"
        }
    )
    
    # 验证响应
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert "No scan configuration found" in response.json()["message"]


def test_webhook_invalid_signature(test_client, mock_github_payload):
    """测试无效签名的情况。"""
    # 发送请求
    response = test_client.post(
        "/scan-trigger",
        json=mock_github_payload,
        headers={
            "X-Hub-Signature-256": "sha256=invalid_signature"
        }
    )
    
    # 验证响应
    assert response.status_code == 401
    assert response.json()["status"] == "error"
    assert "Invalid webhook signature or token" in response.json()["message"]


def test_task_status_endpoint(test_client):
    """测试任务状态端点。"""
    with patch('main.celery_app.AsyncResult') as mock_async_result:
        # 模拟 Celery 任务结果
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = {"coverage_percentage": 85.2}
        mock_async_result.return_value = mock_result
        
        # 发送请求
        response = test_client.get("/task/test-task-id")
        
        # 验证响应
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert response.json()["task_id"] == "test-task-id"
        assert response.json()["result"] == {"coverage_percentage": 85.2}
