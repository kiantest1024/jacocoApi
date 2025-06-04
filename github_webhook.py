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

logger = logging.getLogger(__name__)
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
        hash_name, signature = signature_header.split('=', 1)
        if hash_name != 'sha256':
            return False

        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload_body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"验证 GitHub 签名时出错: {str(e)}")
        return False


def parse_webhook_payload(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    解析 Git webhook 负载（支持 GitHub 和 GitLab）。

    参数:
        payload: Git webhook 负载

    返回:
        (repo_url, commit_id, branch_name, event_type) 的元组
    """
    try:
        # 检查是否为 GitHub ping 事件
        if 'zen' in payload:
            return None, None, None, 'ping'

        # 检查是否为 GitLab webhook
        if 'object_kind' in payload:
            return parse_gitlab_payload(payload)

        # 否则按 GitHub 格式解析
        return parse_github_payload(payload)

    except Exception as e:
        logger.error(f"解析 webhook payload 时出错: {str(e)}")
        return None, None, None, None


def parse_gitlab_payload(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    解析 GitLab webhook 负载。

    参数:
        payload: GitLab webhook 负载

    返回:
        (repo_url, commit_id, branch_name, event_type) 的元组
    """
    try:
        object_kind = payload.get('object_kind')

        if object_kind == 'push':
            # 获取仓库信息
            project = payload.get('project', {})
            repo_url = project.get('http_url') or project.get('ssh_url') or project.get('web_url')

            # 如果没有完整 URL，构造一个
            if not repo_url and project.get('name'):
                project_name = project.get('name')
                user_name = payload.get('user_name', 'user')

                # 特殊处理：如果是 jacocoTest 或 jacocotest 项目，使用已知的完整URL
                if project_name.lower() in ["jacocotest", "jacocoTest"]:
                    # 使用实际的GitLab服务器地址
                    repo_url = f"http://172.16.1.30/{user_name.lower()}/{project_name.lower()}.git"
                    logger.info(f"识别为 jacoco 测试项目，使用配置的 URL: {repo_url}")
                else:
                    # 默认构造逻辑
                    repo_url = f"https://gitlab.com/{user_name}/{project_name}.git"
                    logger.warning(f"GitLab payload 中未找到完整仓库 URL，使用构造的 URL: {repo_url}")

            if not repo_url:
                logger.warning("GitLab payload 中未找到仓库 URL")
                return None, None, None, None

            # 获取分支信息
            ref = payload.get('ref', '')
            if ref.startswith('refs/heads/'):
                branch_name = ref.replace('refs/heads/', '')
            else:
                branch_name = ref

            # 获取最新提交
            commits = payload.get('commits', [])
            if commits:
                commit_id = commits[-1].get('id')
            else:
                commit_id = payload.get('after') or payload.get('checkout_sha')

            return repo_url, commit_id, branch_name, 'push'

        elif object_kind == 'merge_request':
            # 处理 merge request 事件
            merge_request = payload.get('object_attributes', {})
            project = payload.get('project', {})

            repo_url = project.get('http_url') or project.get('ssh_url') or project.get('web_url')
            commit_id = merge_request.get('last_commit', {}).get('id')
            branch_name = merge_request.get('source_branch')

            return repo_url, commit_id, branch_name, 'merge_request'

        else:
            logger.warning(f"不支持的 GitLab 事件类型: {object_kind}")
            return None, None, None, 'unsupported'

    except Exception as e:
        logger.error(f"解析 GitLab payload 时出错: {str(e)}")
        return None, None, None, None


def parse_github_payload(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    解析 GitHub webhook 负载。

    参数:
        payload: GitHub webhook 负载

    返回:
        (repo_url, commit_id, branch_name, event_type) 的元组
    """
    try:
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
async def webhook_handler(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_delivery: Optional[str] = Header(None),
    x_gitlab_event: Optional[str] = Header(None),
    x_gitlab_token: Optional[str] = Header(None)
):
    """
    处理 Git webhook 请求（支持 GitHub 和 GitLab）。

    参数:
        request: FastAPI 请求对象
        x_github_event: GitHub 事件类型
        x_hub_signature_256: GitHub 签名
        x_github_delivery: GitHub 交付 ID
        x_gitlab_event: GitLab 事件类型
        x_gitlab_token: GitLab 令牌

    返回:
        JSON 响应
    """
    # 检测是 GitHub 还是 GitLab webhook
    is_gitlab = x_gitlab_event is not None or x_gitlab_token is not None
    provider = "GitLab" if is_gitlab else "GitHub"
    event_type = x_gitlab_event or x_github_event

    request_id = f"{provider.lower()}_{int(time.time())}_{x_github_delivery or x_gitlab_token or 'unknown'}"
    logger.info(f"[{request_id}] 收到 {provider} webhook: {event_type}")

    try:
        # 读取请求体
        body = await request.body()

        # 验证签名（如果配置了密钥且不是默认值）
        if settings.GIT_WEBHOOK_SECRET and settings.GIT_WEBHOOK_SECRET != "your_default_secret_token":
            if is_gitlab:
                # GitLab 使用简单的 token 验证
                if x_gitlab_token and x_gitlab_token != settings.GIT_WEBHOOK_SECRET:
                    logger.warning(f"[{request_id}] GitLab webhook token 验证失败")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token 验证失败"
                    )
            else:
                # GitHub 使用 HMAC 签名验证
                if x_hub_signature_256 and not verify_github_signature(body, x_hub_signature_256, settings.GIT_WEBHOOK_SECRET):
                    logger.warning(f"[{request_id}] GitHub webhook 签名验证失败")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="签名验证失败"
                    )
        else:
            # 如果使用默认密钥或未配置密钥，跳过验证
            logger.info(f"[{request_id}] 跳过签名验证（使用默认配置或未配置密钥）")
        
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
        if event_type == 'ping' or (is_gitlab and event_type == 'Test Hook'):
            logger.info(f"[{request_id}] {provider} ping/test 事件")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": f"{provider} webhook ping 接收成功"
                }
            )
        
        # 解析负载（支持 GitHub 和 GitLab）
        repo_url, commit_id, branch_name, event_type = parse_webhook_payload(payload)
        
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


@router.post("/webhook-no-auth")
async def webhook_handler_no_auth(request: Request):
    """
    处理 Git webhook 请求（无签名验证）。
    临时端点，用于测试和调试。

    参数:
        request: FastAPI 请求对象

    返回:
        JSON 响应
    """
    request_id = f"noauth_{int(time.time())}_{id(request)}"
    logger.info(f"[{request_id}] 收到无认证 webhook 请求")

    try:
        # 读取请求体
        body = await request.body()

        # 解析 JSON 负载
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            logger.error(f"[{request_id}] 无法解析 JSON 负载")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的 JSON 负载"
            )

        logger.info(f"[{request_id}] 收到负载: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        # 解析负载（支持 GitHub 和 GitLab）
        repo_url, commit_id, branch_name, event_type = parse_webhook_payload(payload)

        logger.info(f"[{request_id}] 解析结果: repo_url={repo_url}, commit_id={commit_id}, branch_name={branch_name}, event_type={event_type}")

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
            logger.error(f"[{request_id}] 无法从 payload 中提取所需信息")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "无法解析 webhook 负载，缺少仓库、提交或分支信息",
                    "extracted": {
                        "repo_url": repo_url,
                        "commit_id": commit_id,
                        "branch_name": branch_name,
                        "event_type": event_type
                    }
                }
            )

        # 获取通用扫描配置（支持所有项目）
        service_config = get_service_config(repo_url)
        service_name = service_config['service_name']
        logger.info(f"[{request_id}] 为项目 {service_name} 生成扫描配置")

        # 发送 JaCoCo 扫描任务
        from jacoco_tasks import run_jacoco_scan_docker

        # 检查是否启用同步模式（用于调试）
        sync_mode = service_config.get('sync_mode', False)

        if sync_mode:
            logger.info(f"[{request_id}] 使用同步模式执行扫描")
            try:
                # 创建临时报告目录
                import tempfile
                reports_dir = tempfile.mkdtemp(prefix=f"jacoco_reports_{request_id}_")

                # 同步执行扫描
                scan_result = run_jacoco_scan_docker(
                    repo_url=repo_url,
                    commit_id=commit_id,
                    branch_name=branch_name,
                    reports_dir=reports_dir,
                    service_config=service_config,
                    request_id=request_id
                )

                logger.info(f"[{request_id}] 同步扫描完成")

                # 返回扫描结果
                response_content = {
                    "status": "completed",
                    "request_id": request_id,
                    "event_type": event_type,
                    "message": f"项目 {service_name} 的提交 {commit_id[:8]} 的 JaCoCo 扫描已完成（同步）",
                    "extracted_info": {
                        "repo_url": repo_url,
                        "commit_id": commit_id,
                        "branch_name": branch_name,
                        "service_name": service_name
                    }
                }

                # 添加扫描结果
                if scan_result:
                    response_content.update(scan_result)

                # 确保通知状态在响应中
                if 'notification_sent' not in response_content:
                    response_content['notification_sent'] = False
                    response_content['notification_status'] = 'unknown'

                logger.info(f"[{request_id}] 同步扫描完成，返回响应")
                logger.info(f"[{request_id}] 响应中的通知状态: notification_sent={response_content.get('notification_sent', 'N/A')}")

                return JSONResponse(
                    status_code=200,
                    content=response_content
                )

            except Exception as e:
                logger.error(f"[{request_id}] 同步扫描失败: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "error",
                        "request_id": request_id,
                        "message": f"扫描失败: {str(e)}"
                    }
                )
        else:
            # 异步执行（使用Celery）
            task = celery_app.send_task(
                'scan_tasks.execute_jacoco_scan',
                args=[repo_url, commit_id, branch_name, service_config],
                kwargs={"request_id": request_id, "event_type": event_type}
            )

            logger.info(f"[{request_id}] JaCoCo 扫描任务已排队: {task.id} 用于项目 {service_name}")

            # 返回成功响应
            return JSONResponse(
                status_code=200,
                content={
                    "status": "accepted",
                    "task_id": task.id,
                    "request_id": request_id,
                    "event_type": event_type,
                    "message": f"项目 {service_name} 的提交 {commit_id[:8]} 的 JaCoCo 扫描任务已成功排队",
                    "extracted_info": {
                        "repo_url": repo_url,
                        "commit_id": commit_id,
                        "branch_name": branch_name,
                        "service_name": service_name
                    }
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] 处理 webhook 时出现意外错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"内部服务器错误: {str(e)}"
        )
