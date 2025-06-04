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
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

# 创建报告存储目录
REPORTS_BASE_DIR = "./reports"
os.makedirs(REPORTS_BASE_DIR, exist_ok=True)

# 挂载静态文件服务（用于HTML报告）
app.mount("/reports", StaticFiles(directory=REPORTS_BASE_DIR), name="reports")

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

def get_server_base_url(request: Request = None) -> str:
    """获取服务器基础URL"""
    if request:
        # 从请求中获取实际的host
        host = request.headers.get("host", "localhost:8002")
        scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
        return f"{scheme}://{host}"
    else:
        # 默认值
        return "http://localhost:8002"

def save_html_report(reports_dir: str, project_name: str, commit_id: str, request_id: str, base_url: str = None) -> str:
    """保存HTML报告并返回访问链接"""
    try:
        import shutil

        # 创建项目报告目录
        project_reports_dir = os.path.join(REPORTS_BASE_DIR, project_name)
        os.makedirs(project_reports_dir, exist_ok=True)

        # 源HTML报告路径
        source_html_dir = os.path.join(reports_dir, "html")
        if not os.path.exists(source_html_dir):
            logger.warning(f"[{request_id}] HTML报告目录不存在: {source_html_dir}")
            return None

        # 目标路径（使用commit_id作为目录名）
        target_html_dir = os.path.join(project_reports_dir, commit_id[:8])

        # 如果目标目录已存在，先删除
        if os.path.exists(target_html_dir):
            shutil.rmtree(target_html_dir)

        # 复制HTML报告
        shutil.copytree(source_html_dir, target_html_dir)

        # 生成访问链接
        relative_url = f"/reports/{project_name}/{commit_id[:8]}/index.html"

        # 如果提供了base_url，生成完整URL，否则返回相对URL
        if base_url:
            full_url = f"{base_url}{relative_url}"
        else:
            full_url = relative_url

        logger.info(f"[{request_id}] HTML报告已保存: {target_html_dir}")
        logger.info(f"[{request_id}] 访问链接: {full_url}")

        return full_url

    except Exception as e:
        logger.error(f"[{request_id}] 保存HTML报告失败: {str(e)}")
        return None

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
def github_webhook_no_auth(request: Request):
    """GitHub/GitLab webhook处理（无认证版本）"""
    try:
        # 生成请求ID
        request_id = f"req_{int(time.time())}"
        
        # 获取请求体 - 同步方式
        import asyncio
        body = asyncio.run(request.body())
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
        
        # 强制使用同步扫描（确保立即执行）
        logger.info(f"[{request_id}] 使用同步扫描模式")

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

            # 调试：显示解析的报告数据
            logger.info(f"[{request_id}] 报告解析结果: {report_data}")

            # 如果解析报告失败但扫描成功，使用扫描结果中的覆盖率数据
            if not report_data.get('reports_available', False) and scan_result.get('status') in ['completed', 'partial']:
                logger.info(f"[{request_id}] 使用扫描结果中的覆盖率数据")
                report_data.update({
                    'coverage_summary': {
                        'instruction_coverage': scan_result.get('instruction_coverage', 0),
                        'branch_coverage': scan_result.get('branch_coverage', 0),
                        'line_coverage': scan_result.get('line_coverage', 0),
                        'complexity_coverage': scan_result.get('complexity_coverage', 0),
                        'method_coverage': scan_result.get('method_coverage', 0),
                        'class_coverage': scan_result.get('class_coverage', 0)
                    }
                })

            # 保存HTML报告并生成访问链接
            base_url = get_server_base_url(request)
            html_report_url = save_html_report(reports_dir, service_name, commit_id, request_id, base_url)

            # 添加HTML报告链接到报告数据
            if html_report_url:
                report_data['html_report_url'] = html_report_url
                logger.info(f"[{request_id}] HTML报告链接: {html_report_url}")

            # 发送通知 - 修改条件，即使没有coverage_summary也发送通知
            webhook_url = service_config.get('notification_webhook')
            if webhook_url:
                try:
                    from feishu_notification import send_jacoco_notification

                    # 确保有coverage_data，如果没有则创建默认的
                    coverage_data = report_data.get('coverage_summary', {
                        'instruction_coverage': 0,
                        'branch_coverage': 0,
                        'line_coverage': 0,
                        'complexity_coverage': 0,
                        'method_coverage': 0,
                        'class_coverage': 0
                    })

                    logger.info(f"[{request_id}] 准备发送Lark通知...")
                    logger.info(f"[{request_id}] Webhook URL: {webhook_url}")
                    logger.info(f"[{request_id}] 覆盖率数据: {coverage_data}")

                    send_jacoco_notification(
                        webhook_url=webhook_url,
                        repo_url=repo_url,
                        branch_name=branch_name,
                        commit_id=commit_id,
                        coverage_data=coverage_data,
                        scan_result=scan_result,
                        request_id=request_id,
                        html_report_url=report_data.get('html_report_url')  # 传递HTML报告链接
                    )
                    logger.info(f"[{request_id}] ✅ 飞书通知已发送")
                except Exception as notify_error:
                    logger.error(f"[{request_id}] ❌ 发送通知失败: {notify_error}")
                    import traceback
                    logger.error(f"[{request_id}] 通知错误详情: {traceback.format_exc()}")
            else:
                logger.warning(f"[{request_id}] 未配置Lark webhook URL，跳过通知发送")

            # 构建响应数据
            response_data = {
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

            logger.info(f"[{request_id}] 同步 JaCoCo 扫描完成")

            # 延迟清理临时目录，避免影响响应
            try:
                # 不立即清理，让系统自动清理临时目录
                logger.info(f"[{request_id}] 临时目录将由系统自动清理: {reports_dir}")
            except Exception as cleanup_error:
                logger.warning(f"[{request_id}] 临时目录清理注意: {cleanup_error}")

            return JSONResponse(
                status_code=200,
                content=response_data
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

@app.get("/reports")
async def list_reports(request: Request):
    """列出所有可用的HTML报告"""
    try:
        reports = []
        base_url = get_server_base_url(request)

        if os.path.exists(REPORTS_BASE_DIR):
            for project_name in os.listdir(REPORTS_BASE_DIR):
                project_dir = os.path.join(REPORTS_BASE_DIR, project_name)
                if os.path.isdir(project_dir):
                    project_reports = []
                    for commit_dir in os.listdir(project_dir):
                        commit_path = os.path.join(project_dir, commit_dir)
                        index_file = os.path.join(commit_path, "index.html")
                        if os.path.isdir(commit_path) and os.path.exists(index_file):
                            # 获取文件修改时间
                            mtime = os.path.getmtime(index_file)
                            relative_url = f"/reports/{project_name}/{commit_dir}/index.html"
                            project_reports.append({
                                "commit_id": commit_dir,
                                "url": relative_url,
                                "full_url": f"{base_url}{relative_url}",
                                "created_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
                            })

                    if project_reports:
                        # 按时间排序，最新的在前
                        project_reports.sort(key=lambda x: x['created_time'], reverse=True)
                        reports.append({
                            "project_name": project_name,
                            "reports": project_reports
                        })

        return {
            "status": "success",
            "total_projects": len(reports),
            "reports": reports,
            "message": "HTML报告列表获取成功"
        }

    except Exception as e:
        logger.error(f"获取报告列表失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"获取报告列表失败: {str(e)}"}
        )

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
    import signal
    import sys

    # 使用固定端口8002避免冲突
    port = 8002

    logger.info("🚀 Starting Universal JaCoCo Scanner API...")
    logger.info(f"📡 Server will be available at: http://localhost:{port}")
    logger.info(f"📖 API documentation: http://localhost:{port}/docs")

    # 设置信号处理器
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在优雅关闭服务...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=port,
            reload=False,  # 禁用reload避免异步问题
            log_level="info",
            access_log=True,
            loop="asyncio"  # 明确指定事件循环
        )
    except KeyboardInterrupt:
        logger.info("🛑 服务被用户中断")
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
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
    finally:
        logger.info("🔚 服务已关闭")

if __name__ == "__main__":
    start_server()
