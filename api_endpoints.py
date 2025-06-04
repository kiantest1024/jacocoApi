import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from config import get_service_config
from jacoco_tasks import celery_app
from security import verify_api_key

router = APIRouter(prefix="/api", tags=["API"])
logger = logging.getLogger(__name__)

class ScanRequest(BaseModel):
    service: str = Field(..., description="服务标识")
    git_repo: str = Field(..., description="Git 仓库地址")
    branch: str = Field("main", description="分支名称")
    commit_id: str = Field(..., description="提交 ID")
    options: Optional[Dict[str, Any]] = Field(None, description="扫描选项")

class ScanResponse(BaseModel):
    task_id: str = Field(..., description="任务 ID")
    status: str = Field(..., description="任务状态")
    message: Optional[str] = Field(None, description="消息")

class TaskStatusResponse(BaseModel):
    task_id: str = Field(..., description="任务 ID")
    status: str = Field(..., description="任务状态")
    result: Optional[Dict[str, Any]] = Field(None, description="扫描结果")
    message: Optional[str] = Field(None, description="消息")


@router.post("/scan", response_model=ScanResponse)
async def trigger_scan(request: ScanRequest, _: str = Depends(verify_api_key)):
    try:
        service_config = get_service_config(request.git_repo)

        task = celery_app.send_task(
            'scan_tasks.execute_scan',
            args=[request.git_repo, request.commit_id, request.branch, service_config],
            kwargs={"request_id": f"api_{request.service}_{request.commit_id[:8]}"}
        )

        logger.info(f"扫描任务已排队: {task.id} 用于 {service_config['service_name']}")

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
async def get_task_status(task_id: str, _: str = Depends(verify_api_key)):
    try:
        task = celery_app.AsyncResult(task_id)

        status_map = {
            'PENDING': ("pending", "任务正在等待执行"),
            'STARTED': ("started", "任务正在进行中"),
            'SUCCESS': ("completed", "任务已成功完成"),
            'FAILURE': ("failed", f"任务失败: {str(task.result)}")
        }

        status_info = status_map.get(task.state, (task.state.lower(), f"任务处于状态: {task.state}"))

        return TaskStatusResponse(
            task_id=task_id,
            status=status_info[0],
            result=task.result if task.state == 'SUCCESS' else None,
            message=status_info[1]
        )

    except Exception as e:
        logger.error(f"获取任务状态时出错: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务状态时出错: {str(e)}"
        )
