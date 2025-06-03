"""
GitHub Webhook 处理器模块。
专门处理来自 GitHub 的 webhook 请求，触发 JaCoCo 覆盖率统计。
"""

import json
import logging
import hashlib
import hmac
import time
from typing import Dict, Any, Optional, Tuple
from fastapi import APIRouter, Request, HTTPException, Header, status
from fastapi.responses import JSONResponse

from config import settings, get_service_config
from jacoco_tasks import celery_app
from security import verify_ip_whitelist

# 设置日志记录器
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/github", tags=["GitHub Webhook"])


def verify_github_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """
    验证 GitHub webhook 签名。
    
    参数:
        payload_body: 请求体的原始字节
        signature_header: GitHub 发送的签名头
        secret: webhook 密钥
        
    返回:
        签名是否有效
    """
    if not signature_header:
        return False
    
    try:
        # GitHub 签名格式: sha256=<signature>
        hash_name, signature = signature_header.split('=', 1)
        if hash_name != 'sha256':
            return False
        
        # 计算预期签名
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload_body,
            hashlib.sha256
        ).hexdigest()
        
        # 使用安全比较
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"验证 GitHub 签名时出错: {str(e)}")
        return False


def parse_github_payload(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    解析 GitHub webhook 负载。
    
    参数:
        payload: GitHub webhook 负载
        
    返回:
        (repo_url, commit_id, branch_name, event_type) 的元组
    """
    try:
        # 检查事件类型
        if 'zen' in payload:
            # ping 事件
            return None, None, None, 'ping'
        
        # 获取仓库信息
        repository = payload.get('repository', {})
        repo_url = repository.get('clone_url') or repository.get('ssh_url')
        
        if not repo_url:
            logger.warning("GitHub payload 中未找到仓库 URL")
            return None, None, None, None
        
        # 处理 push 事件
        if 'commits' in payload and payload.get('ref'):
            ref = payload['ref']
            
            # 检查是否为分支删除
            if payload.get('deleted', False):
                logger.info("忽略分支删除事件")
                return None, None, None, 'branch_deleted'
            
            # 提取分支名称
            if ref.startswith('refs/heads/'):
                branch_name = ref.replace('refs/heads/', '')
            else:
                branch_name = ref
            
            # 获取最新提交
            commits = payload.get('commits', [])
            if commits:
                commit_id = commits[-1].get('id')
            else:
                commit_id = payload.get('after')
            
            return repo_url, commit_id, branch_name, 'push'
        
        # 处理 pull request 事件
        elif 'pull_request' in payload:
            pr = payload['pull_request']
            commit_id = pr['head']['sha']
            branch_name = pr['head']['ref']
            
            return repo_url, commit_id, branch_name, 'pull_request'
        
        else:
            logger.warning(f"不支持的 GitHub 事件类型: {list(payload.keys())}")
            return None, None, None, 'unsupported'
            
    except Exception as e:
        logger.error(f"解析 GitHub payload 时出错: {str(e)}")
        return None, None, None, None


@router.post("/webhook")
async def github_webhook_handler(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_delivery: Optional[str] = Header(None)
):
    """
    处理 GitHub webhook 请求。
    
    参数:
        request: FastAPI 请求对象
        x_github_event: GitHub 事件类型
        x_hub_signature_256: GitHub 签名
        x_github_delivery: GitHub 交付 ID
        
    返回:
        JSON 响应
    """
    request_id = f"github_{int(time.time())}_{x_github_delivery or 'unknown'}"
    logger.info(f"[{request_id}] 收到 GitHub webhook: {x_github_event}")
    
    try:
        # 读取请求体
        body = await request.body()
        
        # 验证签名（如果配置了密钥）
        if settings.GIT_WEBHOOK_SECRET and settings.GIT_WEBHOOK_SECRET != "your_default_secret_token":
            if not verify_github_signature(body, x_hub_signature_256, settings.GIT_WEBHOOK_SECRET):
                logger.warning(f"[{request_id}] GitHub webhook 签名验证失败")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="签名验证失败"
                )
        
        # 解析 JSON 负载
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            logger.error(f"[{request_id}] 无法解析 JSON 负载")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的 JSON 负载"
            )
        
        # 处理 ping 事件
        if x_github_event == 'ping':
            logger.info(f"[{request_id}] GitHub ping 事件")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "GitHub webhook ping 接收成功"
                }
            )
        
        # 解析负载
        repo_url, commit_id, branch_name, event_type = parse_github_payload(payload)
        
        # 处理特殊事件类型
        if event_type in ['branch_deleted', 'unsupported']:
            logger.info(f"[{request_id}] 忽略事件类型: {event_type}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "ignored",
                    "message": f"忽略事件类型: {event_type}"
                }
            )
        
        # 验证提取的信息
        if not repo_url or not commit_id or not branch_name:
            logger.error(f"[{request_id}] 无法从 GitHub payload 中提取所需信息")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法解析 GitHub webhook 负载，缺少仓库、提交或分支信息"
            )
        
        # 查找服务配置
        service_config = get_service_config(repo_url)
        if not service_config:
            logger.info(f"[{request_id}] 未找到仓库的配置: {repo_url}。忽略。")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "ignored",
                    "message": f"未找到仓库 {repo_url} 的扫描配置"
                }
            )
        
        # 将扫描任务发送到 Celery
        task = celery_app.send_task(
            'scan_tasks.execute_jacoco_scan',
            args=[repo_url, commit_id, branch_name, service_config],
            kwargs={"request_id": request_id, "event_type": event_type}
        )
        
        logger.info(f"[{request_id}] JaCoCo 扫描任务已排队: {task.id} 用于 {service_config['service_name']}")
        
        # 返回成功响应
        return JSONResponse(
            status_code=200,
            content={
                "status": "accepted",
                "task_id": task.id,
                "request_id": request_id,
                "event_type": event_type,
                "message": f"服务 {service_config['service_name']} 的提交 {commit_id[:8]} 的 JaCoCo 扫描任务已成功排队"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] 处理 GitHub webhook 时出现意外错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"内部服务器错误: {str(e)}"
        )


@router.get("/test")
async def test_github_webhook():
    """
    测试 GitHub webhook 端点。
    
    返回:
        测试响应
    """
    return {
        "status": "success",
        "message": "GitHub webhook 端点正常工作",
        "timestamp": time.time()
    }
