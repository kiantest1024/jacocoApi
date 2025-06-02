"""
用于 JaCoCo 代码覆盖率扫描的 Celery 任务。
此模块包含用于执行代码覆盖率扫描的 Celery 任务。
"""

import os
import logging
import requests
import datetime
import traceback
from typing import Dict, Any, Optional
from celery import Celery
from celery.signals import task_failure, task_success, task_revoked

from config import settings, CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from scanners import get_scanner_strategy

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# 初始化 Celery 应用
celery_app = Celery(
    'scan_tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Celery 配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 小时
    worker_max_tasks_per_child=100,
    worker_prefetch_multiplier=1,
)

# Celery 任务事件处理程序
@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, **_):
    """记录任务失败。"""
    request_id = kwargs.get('request_id', 'unknown')
    logger.error(
        f"[{request_id}] 任务 {task_id} 失败: {exception}\n"
        f"参数: {args}\n关键字参数: {kwargs}\n"
        f"回溯: {traceback.format_exc()}"
    )

@task_success.connect
def handle_task_success(sender=None, result=None, **kwargs):
    """记录任务成功。"""
    logger.info(f"任务 {sender.request.id} 成功完成，结果: {result}")

@task_revoked.connect
def handle_task_revoked(sender=None, request=None, **kwargs):
    """记录任务撤销。"""
    logger.warning(f"任务 {request.id} 被撤销")

@celery_app.task(name='scan_tasks.execute_scan', bind=True, max_retries=3)
def execute_scan(
    self,
    repo_url: str,
    commit_id: str,
    branch_name: str,
    service_config: Dict[str, Any],
    request_id: str = "unknown"
) -> Dict[str, Any]:
    """
    为指定的仓库和提交执行代码覆盖率扫描。

    参数:
        repo_url: 仓库 URL
        commit_id: 要扫描的提交 ID
        branch_name: 分支名称
        service_config: 服务配置字典
        request_id: 用于跟踪的请求 ID

    返回:
        包含扫描结果的字典
    """
    try:
        logger.info(f"[{request_id}] 开始为 {service_config['service_name']} 扫描 - 提交 {commit_id[:8]} 在分支 {branch_name}")

        # 提取配置
        service_name = service_config.get('service_name', 'unknown')
        scan_method = service_config.get('scan_method', 'default')
        notification_webhook = service_config.get('notification_webhook')

        # 记录开始时间用于指标
        start_time = datetime.datetime.now()

        # 根据扫描方法实现实际的扫描逻辑
        # 这是一个占位符 - 替换为您的实际扫描实现
        scan_result = _perform_scan(repo_url, commit_id, branch_name, scan_method, service_config)

        # 计算持续时间
        duration = (datetime.datetime.now() - start_time).total_seconds()

        # 向扫描结果添加元数据
        scan_result.update({
            "duration_seconds": duration,
            "scan_timestamp": start_time.isoformat(),
            "scan_method": scan_method
        })

        # 如果提供了 webhook URL，则发送通知
        if notification_webhook and scan_result:
            try:
                _send_notification(notification_webhook, service_name, commit_id, branch_name, scan_result, request_id)
            except Exception as notify_err:
                logger.error(f"[{request_id}] 发送通知时出错: {str(notify_err)}")
                # 即使通知失败也继续执行

        logger.info(f"[{request_id}] 扫描完成，服务 {service_name} - 提交 {commit_id[:8]}，用时 {duration:.2f} 秒")
        return {
            "status": "completed",
            "service_name": service_name,
            "commit_id": commit_id,
            "branch_name": branch_name,
            "request_id": request_id,
            "duration_seconds": duration,
            "result": scan_result
        }

    except Exception as e:
        logger.error(f"[{request_id}] 执行扫描时出错: {str(e)}", exc_info=True)
        # 使用指数退避重试任务
        retry_countdown = 60 * (2 ** self.request.retries)  # 60秒, 120秒, 240秒
        logger.info(f"[{request_id}] 将在 {retry_countdown} 秒后重试任务（尝试 {self.request.retries + 1}）")
        self.retry(exc=e, countdown=retry_countdown)


def _perform_scan(repo_url: str, commit_id: str, branch_name: str,
                 scan_method: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据指定的方法执行实际的代码覆盖率扫描。

    参数:
        repo_url: 仓库 URL
        commit_id: 要扫描的提交 ID
        branch_name: 分支名称
        scan_method: 要使用的扫描方法
        service_config: 服务配置字典

    返回:
        包含扫描结果的字典
    """
    logger.info(f"使用方法执行扫描: {scan_method}")

    try:
        # 获取适当的扫描器策略
        scanner = get_scanner_strategy(scan_method)

        # 执行扫描
        result = scanner.scan(repo_url, commit_id, branch_name, service_config)

        # 确保结果包含必要的字段
        if "status" not in result:
            result["status"] = "success"

        return result

    except ValueError as e:
        # 处理未知的扫描方法
        logger.warning(f"未知的扫描方法: {scan_method}，使用默认方法")
        return {
            "coverage_percentage": 0,
            "lines_covered": 0,
            "lines_total": 0,
            "status": "error",
            "message": str(e)
        }

    except Exception as e:
        # 处理扫描过程中的其他错误
        logger.error(f"扫描过程中出错: {str(e)}", exc_info=True)
        return {
            "coverage_percentage": 0,
            "lines_covered": 0,
            "lines_total": 0,
            "status": "error",
            "message": f"扫描过程中出错: {str(e)}"
        }


def _send_notification(
    webhook_url: str,
    service_name: str,
    commit_id: str,
    branch_name: str,
    scan_result: Dict[str, Any],
    request_id: str = "unknown"
) -> None:
    """
    将有关扫描结果的通知发送到指定的 webhook URL。

    参数:
        webhook_url: 要发送通知的 Webhook URL
        service_name: 服务名称
        commit_id: 提交 ID
        branch_name: 分支名称
        scan_result: 扫描结果字典
        request_id: 用于跟踪的请求 ID
    """
    try:
        # 准备通知负载
        payload = {
            "service_name": service_name,
            "commit_id": commit_id,
            "branch_name": branch_name,
            "coverage_percentage": scan_result.get("coverage_percentage", 0),
            "lines_covered": scan_result.get("lines_covered", 0),
            "lines_total": scan_result.get("lines_total", 0),
            "status": scan_result.get("status", "unknown"),
            "scan_method": scan_result.get("scan_method", "unknown"),
            "duration_seconds": scan_result.get("duration_seconds", 0),
            "timestamp": scan_result.get("scan_timestamp", datetime.datetime.now().isoformat()),
            "request_id": request_id
        }

        # 发送带有超时的通知
        response = requests.post(
            webhook_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": f"JaCoCo-Scan-API/{settings.API_VERSION}"
            },
            timeout=10  # 10 秒超时
        )

        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"[{request_id}] 通知成功发送到 {webhook_url}")
        else:
            logger.warning(
                f"[{request_id}] 发送通知失败: {response.status_code} - {response.text}"
            )

    except requests.RequestException as e:
        logger.error(f"[{request_id}] 发送通知时网络错误: {str(e)}")
    except Exception as e:
        logger.error(f"[{request_id}] 发送通知时出错: {str(e)}", exc_info=True)
