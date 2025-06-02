"""
JaCoCo API 端点模块。
提供专用的 API 端点用于触发扫描和查询任务状态。
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from config import get_service_config
from tasks import celery_app
from security import verify_api_key

# 创建路由器
router = APIRouter(prefix="/api", tags=["API"])

# 设置日志记录器
logger = logging.getLogger(__name__)


# 请求模型
class ScanRequest(BaseModel):
    """扫描请求模型。"""
    service: str = Field(..., description="服务标识")
    git_repo: str = Field(..., description="Git 仓库地址")
    branch: str = Field("main", description="分支名称")
    commit_id: str = Field(..., description="提交 ID")
    options: Optional[Dict[str, Any]] = Field(None, description="扫描选项")


# 响应模型
class ScanResponse(BaseModel):
    """扫描响应模型。"""
    task_id: str = Field(..., description="任务 ID")
    status: str = Field(..., description="任务状态")
    message: Optional[str] = Field(None, description="消息")


class TaskStatusResponse(BaseModel):
    """任务状态响应模型。"""
    task_id: str = Field(..., description="任务 ID")
    status: str = Field(..., description="任务状态")
    result: Optional[Dict[str, Any]] = Field(None, description="扫描结果")
    message: Optional[str] = Field(None, description="消息")


@router.post("/scan", response_model=ScanResponse)
async def trigger_scan(
    request: ScanRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    触发代码覆盖率扫描。
    
    参数:
        request: 扫描请求
        api_key: API 密钥
        
    返回:
        扫描响应
    """
    try:
        # 查找服务配置
        service_config = get_service_config(request.git_repo)
        
        # 如果没有找到配置，尝试使用服务名称创建默认配置
        if not service_config:
            service_config = {
                "service_name": request.service,
                "scan_method": "jacoco",
                "docker_image": "jacoco-scanner-ci",
                "incremental_build": True
            }
            
            # 添加请求中的选项
            if request.options:
                service_config.update(request.options)
        
        # 将扫描任务发送到 Celery
        task = celery_app.send_task(
            'scan_tasks.execute_scan',
            args=[request.git_repo, request.commit_id, request.branch, service_config],
            kwargs={"request_id": f"api_{request.service}_{request.commit_id[:8]}"}
        )
        
        logger.info(f"扫描任务已排队: {task.id} 用于 {service_config['service_name']}")
        
        # 返回成功响应
        return ScanResponse(
            task_id=task.id,
            status="queued",
            message=f"服务 {service_config['service_name']} 的提交 {request.commit_id[:8]} 的扫描任务已成功排队"
        )
    
    except Exception as e:
        logger.error(f"触发扫描时出错: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发扫描时出错: {str(e)}"
        )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    获取任务状态。
    
    参数:
        task_id: 任务 ID
        api_key: API 密钥
        
    返回:
        任务状态响应
    """
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = TaskStatusResponse(
                task_id=task_id,
                status="pending",
                message="任务正在等待执行"
            )
        elif task.state == 'STARTED':
            response = TaskStatusResponse(
                task_id=task_id,
                status="started",
                message="任务正在进行中"
            )
        elif task.state == 'SUCCESS':
            response = TaskStatusResponse(
                task_id=task_id,
                status="completed",
                result=task.result,
                message="任务已成功完成"
            )
        elif task.state == 'FAILURE':
            response = TaskStatusResponse(
                task_id=task_id,
                status="failed",
                message=f"任务失败: {str(task.result)}"
            )
        else:
            response = TaskStatusResponse(
                task_id=task_id,
                status=task.state.lower(),
                message=f"任务处于状态: {task.state}"
            )
        
        return response
    
    except Exception as e:
        logger.error(f"获取任务状态时出错: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务状态时出错: {str(e)}"
        )
