"""
Celery 任务的单元测试。
"""

from unittest.mock import patch, MagicMock

import pytest
from celery.exceptions import Retry

from tasks import execute_scan, _perform_scan, _send_notification


@patch('tasks._perform_scan')
@patch('tasks._send_notification')
def test_execute_scan(mock_send_notification, mock_perform_scan):
    """测试执行扫描任务。"""
    # 设置模拟返回值
    mock_perform_scan.return_value = {
        "status": "success",
        "coverage_percentage": 85.2,
        "lines_covered": 1250,
        "lines_total": 1468
    }
    
    # 创建任务实例
    task = MagicMock()
    task.request.retries = 0
    
    # 测试执行扫描
    service_config = {
        "service_name": "test-service",
        "scan_method": "solution1",
        "notification_webhook": "http://test.webhook.url"
    }
    
    result = execute_scan(
        task,
        "git@example.com:user/repo.git",
        "abcdef",
        "main",
        service_config,
        "test-request-id"
    )
    
    # 验证结果
    assert result["status"] == "completed"
    assert result["service_name"] == "test-service"
    assert result["commit_id"] == "abcdef"
    assert result["branch_name"] == "main"
    assert result["request_id"] == "test-request-id"
    assert "duration_seconds" in result
    assert result["result"]["status"] == "success"
    assert result["result"]["coverage_percentage"] == 85.2
    
    # 验证调用
    mock_perform_scan.assert_called_once_with(
        "git@example.com:user/repo.git",
        "abcdef",
        "main",
        "solution1",
        service_config
    )
    
    mock_send_notification.assert_called_once()
    args, kwargs = mock_send_notification.call_args
    assert args[0] == "http://test.webhook.url"
    assert args[1] == "test-service"
    assert args[2] == "abcdef"
    assert args[3] == "main"
    assert args[5] == "test-request-id"


@patch('tasks._perform_scan')
def test_execute_scan_error(mock_perform_scan):
    """测试执行扫描任务出错。"""
    # 设置模拟返回值
    mock_perform_scan.side_effect = Exception("Scan failed")
    
    # 创建任务实例
    task = MagicMock()
    task.request.retries = 0
    task.retry.side_effect = Retry()
    
    # 测试执行扫描
    service_config = {
        "service_name": "test-service",
        "scan_method": "solution1",
        "notification_webhook": "http://test.webhook.url"
    }
    
    # 应该重试任务
    with pytest.raises(Retry):
        execute_scan(
            task,
            "git@example.com:user/repo.git",
            "abcdef",
            "main",
            service_config,
            "test-request-id"
        )
    
    # 验证调用
    mock_perform_scan.assert_called_once()
    task.retry.assert_called_once()


@patch('tasks.get_scanner_strategy')
def test_perform_scan(mock_get_scanner_strategy):
    """测试执行扫描。"""
    # 设置模拟返回值
    mock_scanner = MagicMock()
    mock_scanner.scan.return_value = {
        "status": "success",
        "coverage_percentage": 85.2,
        "lines_covered": 1250,
        "lines_total": 1468
    }
    mock_get_scanner_strategy.return_value = mock_scanner
    
    # 测试执行扫描
    service_config = {
        "service_name": "test-service",
        "scan_method": "solution1",
        "notification_webhook": "http://test.webhook.url"
    }
    
    result = _perform_scan(
        "git@example.com:user/repo.git",
        "abcdef",
        "main",
        "solution1",
        service_config
    )
    
    # 验证结果
    assert result["status"] == "success"
    assert result["coverage_percentage"] == 85.2
    assert result["lines_covered"] == 1250
    assert result["lines_total"] == 1468
    
    # 验证调用
    mock_get_scanner_strategy.assert_called_once_with("solution1")
    mock_scanner.scan.assert_called_once_with(
        "git@example.com:user/repo.git",
        "abcdef",
        "main",
        service_config
    )


@patch('tasks.get_scanner_strategy')
def test_perform_scan_unknown_method(mock_get_scanner_strategy):
    """测试执行未知扫描方法。"""
    # 设置模拟返回值
    mock_get_scanner_strategy.side_effect = ValueError("Unknown scan method")
    
    # 测试执行扫描
    result = _perform_scan(
        "git@example.com:user/repo.git",
        "abcdef",
        "main",
        "unknown",
        {}
    )
    
    # 验证结果
    assert result["status"] == "error"
    assert "message" in result
    assert result["coverage_percentage"] == 0
    assert result["lines_covered"] == 0
    assert result["lines_total"] == 0
    
    # 验证调用
    mock_get_scanner_strategy.assert_called_once_with("unknown")


@patch('requests.post')
def test_send_notification(mock_post):
    """测试发送通知。"""
    # 设置模拟返回值
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    # 测试发送通知
    scan_result = {
        "status": "success",
        "coverage_percentage": 85.2,
        "lines_covered": 1250,
        "lines_total": 1468,
        "scan_method": "solution1",
        "duration_seconds": 45.2,
        "scan_timestamp": "2023-05-10T12:34:56.789Z"
    }
    
    _send_notification(
        "http://test.webhook.url",
        "test-service",
        "abcdef",
        "main",
        scan_result,
        "test-request-id"
    )
    
    # 验证调用
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "http://test.webhook.url"
    assert kwargs["json"]["service_name"] == "test-service"
    assert kwargs["json"]["commit_id"] == "abcdef"
    assert kwargs["json"]["branch_name"] == "main"
    assert kwargs["json"]["coverage_percentage"] == 85.2
    assert kwargs["json"]["lines_covered"] == 1250
    assert kwargs["json"]["lines_total"] == 1468
    assert kwargs["json"]["status"] == "success"
    assert kwargs["json"]["scan_method"] == "solution1"
    assert kwargs["json"]["duration_seconds"] == 45.2
    assert kwargs["json"]["request_id"] == "test-request-id"
    assert "timeout" in kwargs


@patch('requests.post')
def test_send_notification_error(mock_post):
    """测试发送通知出错。"""
    # 设置模拟返回值
    mock_post.side_effect = Exception("Request failed")
    
    # 测试发送通知
    scan_result = {
        "status": "success",
        "coverage_percentage": 85.2,
        "lines_covered": 1250,
        "lines_total": 1468
    }
    
    # 不应该引发异常
    _send_notification(
        "http://test.webhook.url",
        "test-service",
        "abcdef",
        "main",
        scan_result,
        "test-request-id"
    )
    
    # 验证调用
    mock_post.assert_called_once()
