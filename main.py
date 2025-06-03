"""
JaCoCo 扫描触发 API 的主 FastAPI 应用程序。
此模块包含 FastAPI 应用程序和 webhook 接收器的路由。
"""

import logging
import time

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry

from config import settings
from jacoco_tasks import celery_app
from security import verify_api_key, rate_limiter, create_security_middleware
from logging_config import setup_logging
from api_endpoints import router as api_router
from github_webhook import router as github_router

# 设置日志配置
setup_logging()

# 创建自定义注册表以避免重复
registry = CollectorRegistry()

# 定义 Prometheus 指标
WEBHOOK_COUNTER = Counter(
    'webhook_requests_total',
    '总 webhook 请求数',
    ['provider', 'status'],
    registry=registry
)

SCAN_DURATION = Histogram(
    'scan_duration_seconds',
    '扫描持续时间（秒）',
    ['service', 'method'],
    registry=registry
)

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# 初始化 FastAPI 应用
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url=None,  # 禁用默认文档
    redoc_url=None,  # 禁用默认 redoc
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# 添加 API 路由
app.include_router(api_router)
app.include_router(github_router)

# 使用从 security 模块导入的速率限制器
if settings.RATE_LIMIT_ENABLED:
    def rate_limit():
        return Depends(rate_limiter)
else:
    # 禁用时的空操作速率限制器
    def rate_limit():
        return None

# 添加安全中间件
app.middleware("http")(create_security_middleware())

# 添加受信任主机中间件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_ORIGINS if "*" not in settings.ALLOWED_ORIGINS else ["*"]
)

# 自定义 API 文档路由
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """自定义 Swagger UI 路由。"""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.API_TITLE} - Swagger UI",
        oauth2_redirect_url="/docs/oauth2-redirect",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    """OpenAPI 架构端点。"""
    return get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=settings.API_DESCRIPTION,
        routes=app.routes,
    )

# Prometheus 指标端点
@app.get("/metrics")
async def metrics():
    """Prometheus 指标端点。"""
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点，用于验证 API 是否正在运行。"""
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "timestamp": time.time()
    }

# 任务状态端点（需要 API 密钥认证）
@app.get("/task/{task_id}", dependencies=[Depends(verify_api_key)])
async def get_task_status(task_id: str):
    """
    获取扫描任务的状态。

    参数:
        task_id: Celery 任务 ID

    返回:
        带有任务状态的 JSON 响应
    """
    try:
        task = celery_app.AsyncResult(task_id)

        if task.state == 'PENDING':
            response = {
                "status": "pending",
                "task_id": task_id,
                "message": "任务正在等待执行"
            }
        elif task.state == 'STARTED':
            response = {
                "status": "started",
                "task_id": task_id,
                "message": "任务正在进行中"
            }
        elif task.state == 'SUCCESS':
            response = {
                "status": "completed",
                "task_id": task_id,
                "result": task.result,
                "message": "任务已成功完成"
            }
        elif task.state == 'FAILURE':
            response = {
                "status": "failed",
                "task_id": task_id,
                "error": str(task.result),
                "message": "任务失败"
            }
        else:
            response = {
                "status": task.state.lower(),
                "task_id": task_id,
                "message": f"任务处于状态: {task.state}"
            }

        return JSONResponse(status_code=200, content=response)

    except Exception as e:
        logger.error(f"检索任务状态时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检索任务状态时出错: {str(e)}")

# 注意: 旧的 /scan-trigger 端点已被 GitHub webhook 端点替代
# 请使用 /github/webhook 端点来接收 GitHub webhook 事件

# HTTP 异常的错误处理程序
@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    """HTTP 异常的自定义异常处理程序。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail}
    )

# 通用错误处理程序
@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception):
    """所有其他异常的通用异常处理程序。"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "内部服务器错误"}
    )

# 当直接执行时，使用 uvicorn 运行应用程序
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG
    )
