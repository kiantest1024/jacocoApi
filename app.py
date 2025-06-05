import os
import logging
import time
import json
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="JaCoCo Scanner API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

REPORTS_BASE_DIR = "./reports"
os.makedirs(REPORTS_BASE_DIR, exist_ok=True)
app.mount("/reports", StaticFiles(directory=REPORTS_BASE_DIR), name="reports")

def get_service_config(repo_url: str) -> Dict[str, Any]:
    from config import get_service_config as config_get_service_config
    return config_get_service_config(repo_url)

def get_server_base_url(request: Request = None) -> str:
    if request:
        host = request.headers.get("host", "localhost:8002")
        scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
        return f"{scheme}://{host}"
    return "http://localhost:8002"

def save_html_report(reports_dir: str, project_name: str, commit_id: str, request_id: str, base_url: str = None) -> str:
    try:
        import shutil
        project_reports_dir = os.path.join(REPORTS_BASE_DIR, project_name)
        os.makedirs(project_reports_dir, exist_ok=True)

        source_html_dir = os.path.join(reports_dir, "html")
        if not os.path.exists(source_html_dir):
            logger.warning(f"[{request_id}] HTML报告目录不存在: {source_html_dir}")
            return None

        target_html_dir = os.path.join(project_reports_dir, commit_id[:8])
        if os.path.exists(target_html_dir):
            shutil.rmtree(target_html_dir)

        shutil.copytree(source_html_dir, target_html_dir)
        relative_url = f"/reports/{project_name}/{commit_id[:8]}/index.html"
        full_url = f"{base_url}{relative_url}" if base_url else relative_url

        logger.info(f"[{request_id}] HTML报告已保存: {target_html_dir}")
        return full_url
    except Exception as e:
        logger.error(f"[{request_id}] 保存HTML报告失败: {str(e)}")
        return None

# 路由
@app.get("/")
async def root():
    return {
        "message": "JaCoCo Scanner API",
        "version": "2.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "JaCoCo Scanner"
    }

@app.post("/github/webhook-no-auth")
def github_webhook_no_auth(request: Request):
    try:
        request_id = f"req_{int(time.time())}"

        import asyncio
        try:
            loop = asyncio.get_running_loop()
            body = loop.run_until_complete(request.body())
        except RuntimeError:
            body = asyncio.run(request.body())

        if not body:
            raise HTTPException(status_code=400, detail="Empty request body")

        payload = json.loads(body)
        event_type = "unknown"
        repo_url = None
        commit_id = None
        branch_name = "main"
        if "object_kind" in payload:
            event_type = "gitlab_push"
            if payload.get("object_kind") == "push":
                project = payload.get("project", {})
                project_name = project.get("name", "unknown")
                user_name = payload.get("user_name", "user")

                repo_url = project.get("http_url") or project.get("ssh_url") or project.get("web_url")
                if not repo_url:
                    if project_name.lower() in ["jacocotest", "jacocoTest"]:
                        repo_url = f"http://172.16.1.30/{user_name.lower()}/{project_name.lower()}.git"
                    else:
                        repo_url = f"http://172.16.1.30/{user_name}/{project_name}.git"

                commits = payload.get("commits", [])
                commit_id = commits[0].get("id", "unknown") if commits else payload.get("after", "unknown")
                ref = payload.get("ref", "refs/heads/main")
                branch_name = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else "main"

        elif "repository" in payload:
            event_type = "github_push"
            repo_url = payload.get("repository", {}).get("clone_url")
            commit_id = payload.get("after", "unknown")
            ref = payload.get("ref", "refs/heads/main")
            branch_name = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else "main"
        
        if not repo_url:
            raise HTTPException(status_code=400, detail="Cannot extract repository URL from webhook")

        service_config = get_service_config(repo_url)
        service_name = service_config['service_name']

        logger.info(f"[{request_id}] Webhook received: {event_type}")
        logger.info(f"[{request_id}] Repository: {repo_url}")
        logger.info(f"[{request_id}] Project: {service_name}")
        logger.info(f"[{request_id}] Commit: {commit_id}")
        logger.info(f"[{request_id}] Branch: {branch_name}")

        logger.info(f"[{request_id}] 使用同步扫描模式")

        try:
            from jacoco_tasks import run_jacoco_scan_docker, parse_jacoco_reports
            import tempfile

            reports_dir = tempfile.mkdtemp(prefix=f"jacoco_reports_{request_id}_")
            logger.info(f"[{request_id}] 开始同步 JaCoCo 扫描...")

            scan_result = run_jacoco_scan_docker(
                repo_url, commit_id, branch_name, reports_dir, service_config, request_id
            )

            report_data = parse_jacoco_reports(reports_dir, request_id)
            logger.info(f"[{request_id}] 报告解析结果: {report_data}")

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

            base_url = get_server_base_url(request)
            html_report_url = save_html_report(reports_dir, service_name, commit_id, request_id, base_url)

            if html_report_url:
                report_data['html_report_url'] = html_report_url
                logger.info(f"[{request_id}] HTML报告链接: {html_report_url}")

            webhook_url = service_config.get('notification_webhook')
            if webhook_url:
                try:
                    from lark_notification import send_jacoco_notification

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
                        html_report_url=report_data.get('html_report_url')
                    )
                    logger.info(f"[{request_id}] ✅ lark通知已发送")
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

            try:
                logger.info(f"[{request_id}] 临时目录将由系统自动清理: {reports_dir}")
            except Exception as cleanup_error:
                logger.warning(f"[{request_id}] 临时目录清理注意: {cleanup_error}")

            return JSONResponse(
                status_code=200,
                content=response_data
            )

        except Exception as sync_error:
            logger.error(f"[{request_id}] 同步扫描失败: {sync_error}")

            return JSONResponse(
                    status_code=200,
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
                            mtime = os.path.getmtime(index_file)
                            relative_url = f"/reports/{project_name}/{commit_dir}/index.html"
                            project_reports.append({
                                "commit_id": commit_dir,
                                "url": relative_url,
                                "full_url": f"{base_url}{relative_url}",
                                "created_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
                            })

                    if project_reports:
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
    import uvicorn
    import signal
    import sys

    port = 8002

    logger.info("🚀 Starting JaCoCo Scanner API...")
    logger.info(f"📡 Server: http://localhost:{port}")
    logger.info(f"📖 Docs: http://localhost:{port}/docs")

    def signal_handler(signum, _):
        logger.info(f"收到信号 {signum}，正在优雅关闭服务...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level="info",
            access_log=True,
            loop="asyncio"
        )
    except KeyboardInterrupt:
        logger.info("🛑 服务被用户中断")
    except OSError as e:
        if "10048" in str(e):
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
