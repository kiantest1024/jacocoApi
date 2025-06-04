#!/usr/bin/env python3
"""
Universal JaCoCo Scanner API - 独立启动版本
"""

import os
import logging
import time
import json
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# 配置
class Config:
    API_TITLE = "Universal JaCoCo Scanner API"
    API_DESCRIPTION = "Universal JaCoCo coverage scanner for any Maven project"
    API_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

config = Config()

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI应用
app = FastAPI(
    title=config.API_TITLE,
    description=config.API_DESCRIPTION,
    version=config.API_VERSION,
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# 通用配置
DEFAULT_SCAN_CONFIG = {
    "scan_method": "jacoco",
    "project_type": "maven",
    "docker_image": "jacoco-scanner:latest",
    "notification_webhook": "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe",
    "coverage_threshold": 50.0,
    "maven_goals": ["clean", "test", "jacoco:report"],
    "report_formats": ["xml", "html", "json"],
    "use_docker": True,
    "use_incremental_update": True,
    "scan_timeout": 1800,
    "max_retries": 3,
}

def get_project_name_from_url(repo_url: str) -> str:
    """从仓库URL提取项目名称"""
    url = repo_url.replace('.git', '')
    if '/' in url:
        return url.split('/')[-1]
    return url

def get_service_config(repo_url: str) -> Dict[str, Any]:
    """获取服务配置"""
    project_name = get_project_name_from_url(repo_url)
    config = DEFAULT_SCAN_CONFIG.copy()
    config.update({
        "service_name": project_name,
        "repo_url": repo_url,
        "local_repo_path": f"./repos/{project_name}",
    })
    return config

# 路由
@app.get("/")
async def root():
    return {
        "message": "Universal JaCoCo Scanner API is running",
        "version": config.API_VERSION,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": config.API_VERSION,
        "timestamp": time.time(),
        "service": "Universal JaCoCo Scanner"
    }

@app.post("/github/webhook-no-auth")
async def github_webhook_no_auth(request: Request):
    """GitHub/GitLab webhook处理（无认证版本）"""
    try:
        # 生成请求ID
        request_id = f"req_{int(time.time())}"
        
        # 获取请求体
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Empty request body")
        
        payload = json.loads(body)
        
        # 检测webhook类型
        event_type = "unknown"
        repo_url = None
        commit_id = None
        branch_name = "main"
        
        # GitLab webhook
        if "object_kind" in payload:
            event_type = "gitlab_push"
            if payload.get("object_kind") == "push":
                project = payload.get("project", {})
                project_name = project.get("name", "unknown")
                user_name = payload.get("user_name", "user")

                # 尝试获取完整URL，如果没有则构造一个
                repo_url = project.get("http_url") or project.get("ssh_url") or project.get("web_url")
                if not repo_url:
                    # 构造默认URL（基于您的GitLab服务器）
                    if project_name.lower() in ["jacocotest", "jacocoTest"]:
                        repo_url = f"http://172.16.1.30/{user_name.lower()}/{project_name.lower()}.git"
                    else:
                        repo_url = f"http://172.16.1.30/{user_name}/{project_name}.git"

                commits = payload.get("commits", [])
                if commits:
                    commit_id = commits[0].get("id", "unknown")
                else:
                    commit_id = payload.get("after", "unknown")

                ref = payload.get("ref", "refs/heads/main")
                branch_name = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else "main"
        
        # GitHub webhook
        elif "repository" in payload:
            event_type = "github_push"
            repo_url = payload.get("repository", {}).get("clone_url")
            commit_id = payload.get("after", "unknown")
            ref = payload.get("ref", "refs/heads/main")
            branch_name = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else "main"
        
        if not repo_url:
            raise HTTPException(status_code=400, detail="Cannot extract repository URL from webhook")
        
        # 获取配置
        service_config = get_service_config(repo_url)
        service_name = service_config['service_name']
        
        logger.info(f"[{request_id}] Webhook received: {event_type}")
        logger.info(f"[{request_id}] Repository: {repo_url}")
        logger.info(f"[{request_id}] Project: {service_name}")
        logger.info(f"[{request_id}] Commit: {commit_id}")
        logger.info(f"[{request_id}] Branch: {branch_name}")
        
        # 尝试异步扫描，如果失败则使用同步扫描
        try:
            # 尝试导入Celery任务
            from jacoco_tasks import run_docker_jacoco_scan

            # 异步任务
            task = run_docker_jacoco_scan.delay(
                repo_url=repo_url,
                commit_id=commit_id,
                branch_name=branch_name,
                service_config=service_config,
                request_id=request_id
            )

            logger.info(f"[{request_id}] JaCoCo 扫描任务已排队: {task.id} 用于项目 {service_name}")

            return JSONResponse(
                status_code=200,
                content={
                    "status": "accepted",
                    "task_id": task.id,
                    "request_id": request_id,
                    "event_type": event_type,
                    "message": f"项目 {service_name} 的提交 {commit_id[:8]} 的 JaCoCo 扫描任务已成功排队（异步）",
                    "extracted_info": {
                        "repo_url": repo_url,
                        "commit_id": commit_id,
                        "branch_name": branch_name,
                        "service_name": service_name
                    }
                }
            )

        except Exception as celery_error:
            logger.warning(f"[{request_id}] Celery 不可用，使用同步扫描: {celery_error}")

            # 同步扫描
            try:
                from jacoco_tasks import run_jacoco_scan_docker, parse_jacoco_reports
                import tempfile
                import shutil

                # 创建临时报告目录
                reports_dir = tempfile.mkdtemp(prefix=f"jacoco_reports_{request_id}_")
                logger.info(f"[{request_id}] 开始同步 JaCoCo 扫描...")

                # 执行扫描
                scan_result = run_jacoco_scan_docker(
                    repo_url, commit_id, branch_name, reports_dir, service_config, request_id
                )

                # 解析报告
                report_data = parse_jacoco_reports(reports_dir, request_id)

                # 发送通知
                webhook_url = service_config.get('notification_webhook')
                if webhook_url and 'coverage_summary' in report_data:
                    try:
                        from feishu_notification import send_jacoco_notification
                        send_jacoco_notification(
                            webhook_url=webhook_url,
                            repo_url=repo_url,
                            branch_name=branch_name,
                            commit_id=commit_id,
                            coverage_data=report_data['coverage_summary'],
                            scan_result=scan_result,
                            request_id=request_id
                        )
                        logger.info(f"[{request_id}] 飞书通知已发送")
                    except Exception as notify_error:
                        logger.warning(f"[{request_id}] 发送通知失败: {notify_error}")

                # 清理临时目录
                try:
                    shutil.rmtree(reports_dir)
                except Exception as cleanup_error:
                    logger.warning(f"[{request_id}] 清理临时目录失败: {cleanup_error}")

                logger.info(f"[{request_id}] 同步 JaCoCo 扫描完成")

                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "completed",
                        "request_id": request_id,
                        "event_type": event_type,
                        "message": f"项目 {service_name} 的提交 {commit_id[:8]} 的 JaCoCo 扫描已完成（同步）",
                        "scan_result": scan_result,
                        "report_data": report_data,
                        "extracted_info": {
                            "repo_url": repo_url,
                            "commit_id": commit_id,
                            "branch_name": branch_name,
                            "service_name": service_name
                        }
                    }
                )

            except Exception as sync_error:
                logger.error(f"[{request_id}] 同步扫描失败: {sync_error}")

                # 返回错误但不中断服务
                return JSONResponse(
                    status_code=200,  # 仍返回200，表示webhook接收成功
                    content={
                        "status": "error",
                        "request_id": request_id,
                        "message": f"JaCoCo 扫描失败: {str(sync_error)}",
                        "error_details": str(sync_error),
                        "extracted_info": {
                            "repo_url": repo_url,
                            "commit_id": commit_id,
                            "branch_name": branch_name,
                            "service_name": service_name
                        },
                        "note": "Webhook接收成功，但扫描执行失败。请检查Docker环境和网络连接。"
                    }
                )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"[{request_id}] Webhook processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

@app.get("/config/test")
async def test_config():
    """测试配置功能"""
    test_url = "https://github.com/user/test-project.git"
    config = get_service_config(test_url)
    
    return {
        "test_url": test_url,
        "generated_config": config,
        "message": "通用配置功能正常"
    }

# 异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"}
    )

def start_server():
    """启动服务器"""
    import uvicorn

    # 使用固定端口8002避免冲突
    port = 8002

    logger.info("🚀 Starting Universal JaCoCo Scanner API...")
    logger.info(f"📡 Server will be available at: http://localhost:{port}")
    logger.info(f"📖 API documentation: http://localhost:{port}/docs")

    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=port,
            reload=config.DEBUG,
            log_level="info"
        )
    except OSError as e:
        if "10048" in str(e):  # 端口被占用
            logger.error(f"❌ 端口 {port} 被占用")
            logger.info("💡 请尝试以下解决方案:")
            logger.info(f"   1. 使用命令: python -m uvicorn app:app --host 0.0.0.0 --port 8003")
            logger.info(f"   2. 或者重启计算机释放端口")
        else:
            logger.error(f"❌ 启动失败: {e}")
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    start_server()
