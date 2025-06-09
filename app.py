import os
import logging
import time
import json
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="JaCoCo Scanner API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

templates = Jinja2Templates(directory="static/templates")
CONFIG_STORAGE_TYPE = os.getenv('CONFIG_STORAGE_TYPE', 'file')

def init_config_manager():
    """初始化配置管理器"""
    global CONFIG_MANAGER_TYPE

    if CONFIG_STORAGE_TYPE == 'mysql':
        try:
            from src.database import init_database
            from src.mysql_config_manager import get_mysql_config_manager

            logger.info("正在初始化MySQL配置管理器...")
            if init_database():
                # 测试MySQL连接
                mysql_manager = get_mysql_config_manager()
                status = mysql_manager.get_config_status()
                logger.info(f"✅ MySQL配置管理已启用 - {status.get('storage_type', 'MySQL')}")
                CONFIG_MANAGER_TYPE = 'mysql'
                return True
            else:
                logger.warning("❌ MySQL初始化失败，回退到文件配置")
                CONFIG_MANAGER_TYPE = 'file'
                return False
        except Exception as e:
            logger.error(f"❌ MySQL配置管理器初始化失败: {e}")
            logger.warning("回退到文件配置")
            CONFIG_MANAGER_TYPE = 'file'
            return False

    elif os.path.exists("/app/config"):
        try:
            from src.docker_config_manager import init_docker_config, get_docker_config_manager
            init_docker_config()
            logger.info("✅ Docker配置管理已启用")
            CONFIG_MANAGER_TYPE = 'docker'
            return True
        except Exception as e:
            logger.error(f"❌ Docker配置管理器初始化失败: {e}")
            CONFIG_MANAGER_TYPE = 'file'
            return False
    else:
        logger.info("✅ 使用文件配置管理")
        CONFIG_MANAGER_TYPE = 'file'
        return True

CONFIG_MANAGER_TYPE = 'file'
config_init_success = init_config_manager()

if not config_init_success:
    logger.warning("配置管理器初始化失败，使用文件配置作为回退方案")

class ProjectMapping(BaseModel):
    project_name: str
    git_url: str
    bot_id: str
    webhook_url: str = None

class DeleteMapping(BaseModel):
    pattern: str

class CustomBot(BaseModel):
    name: str
    webhook_url: str

class BatchProjects(BaseModel):
    projects: list
    default_bot_id: str = "default"

class AdminAction(BaseModel):
    password: str
    action: str
    data: dict = None

REPORTS_BASE_DIR = "./reports"
os.makedirs(REPORTS_BASE_DIR, exist_ok=True)
app.mount("/reports", StaticFiles(directory=REPORTS_BASE_DIR), name="reports")

def get_config_manager():
    """获取当前配置管理器"""
    if CONFIG_MANAGER_TYPE == 'mysql':
        from src.mysql_config_manager import get_mysql_config_manager
        return get_mysql_config_manager()
    elif CONFIG_MANAGER_TYPE == 'docker':
        from src.docker_config_manager import get_docker_config_manager
        return get_docker_config_manager()
    else:
        # 返回文件配置管理器的包装器
        return FileConfigWrapper()

class FileConfigWrapper:

    def get_lark_bots(self):
        from config.config import list_all_bots
        return list_all_bots()

    def get_project_mappings(self):
        from config.config import list_project_mappings
        return list_project_mappings()

    def add_bot(self, bot_id: str, bot_config: dict) -> bool:
        try:
            from config import config
            config.LARK_BOTS[bot_id] = bot_config
            return True
        except Exception:
            return False

    def remove_bot(self, bot_id: str) -> bool:
        try:
            from config import config
            if bot_id in config.LARK_BOTS and config.LARK_BOTS[bot_id].get('is_custom', False):
                del config.LARK_BOTS[bot_id]
                return True
            return False
        except Exception:
            return False

    def add_project_mapping(self, project_name: str, bot_id: str, git_url: str = None) -> bool:
        try:
            from config import config
            config.PROJECT_BOT_MAPPING[project_name] = bot_id
            return True
        except Exception:
            return False

    def delete_project_mapping(self, project_name: str) -> bool:
        try:
            from config import config
            if project_name in config.PROJECT_BOT_MAPPING:
                del config.PROJECT_BOT_MAPPING[project_name]
                return True
            return False
        except Exception:
            return False

    def check_project_exists(self, project_name: str) -> dict:
        try:
            from config.config import check_project_exists
            return check_project_exists(project_name)
        except Exception:
            return {"exists": False}

    def verify_admin_password(self, password: str) -> bool:
        try:
            from config.config import verify_admin_password
            return verify_admin_password(password)
        except Exception:
            return False

    def get_config_status(self) -> dict:
        try:
            from config.config import list_all_bots, list_project_mappings
            bots = list_all_bots()
            mappings = list_project_mappings()
            return {
                "storage_type": "File",
                "total_bots": len(bots),
                "total_mappings": len(mappings),
                "custom_bots": sum(1 for bot in bots.values() if bot.get('is_custom', False)),
                "environment": "Local",
                "persistent": False
            }
        except Exception as e:
            return {"error": str(e)}

def get_service_config(repo_url: str) -> Dict[str, Any]:
    from config.config import get_service_config as config_get_service_config
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

@app.get("/")
async def root():
    return {
        "message": "JaCoCo Scanner API",
        "version": "2.0.0",
        "docs": "/docs",
        "config": "/config"
    }

@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    return templates.TemplateResponse("config.html", {"request": request})

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
            from src.jacoco_tasks import run_jacoco_scan_docker, parse_jacoco_reports
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

            # 发送Lark通知
            if service_config.get('enable_notifications', True):
                try:
                    from src.lark_notification import send_jacoco_notification

                    coverage_data = report_data.get('coverage_summary', {
                        'instruction_coverage': 0,
                        'branch_coverage': 0,
                        'line_coverage': 0,
                        'complexity_coverage': 0,
                        'method_coverage': 0,
                        'class_coverage': 0
                    })

                    bot_id = service_config.get('bot_id', 'default')
                    bot_name = service_config.get('bot_name', '默认机器人')
                    webhook_url = service_config.get('notification_webhook')

                    logger.info(f"[{request_id}] 准备发送Lark通知...")
                    logger.info(f"[{request_id}] 目标机器人: {bot_name} (ID: {bot_id})")
                    logger.info(f"[{request_id}] Webhook URL: {webhook_url}")
                    logger.info(f"[{request_id}] 覆盖率数据: {coverage_data}")

                    send_jacoco_notification(
                        repo_url=repo_url,
                        branch_name=branch_name,
                        commit_id=commit_id,
                        coverage_data=coverage_data,
                        scan_result=scan_result,
                        request_id=request_id,
                        html_report_url=report_data.get('html_report_url'),
                        webhook_url=webhook_url,
                        bot_id=bot_id
                    )
                    logger.info(f"[{request_id}] ✅ lark通知已发送到 {bot_name}")
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

@app.get("/config/bots")
async def list_bots():
    """列出所有配置的Lark机器人"""
    try:
        config_manager = get_config_manager()
        bots = config_manager.get_lark_bots()
        return {
            "status": "success",
            "total_bots": len(bots),
            "bots": bots,
            "message": "机器人列表获取成功"
        }
    except Exception as e:
        logger.error(f"获取机器人列表失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"获取机器人列表失败: {str(e)}"}
        )

@app.get("/config/mappings")
async def list_mappings():
    """列出所有项目与机器人的映射关系"""
    try:
        config_manager = get_config_manager()
        mappings = config_manager.get_project_mappings()
        return {
            "status": "success",
            "total_mappings": len(mappings),
            "mappings": mappings,
            "message": "项目映射列表获取成功"
        }
    except Exception as e:
        logger.error(f"获取项目映射失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"获取项目映射失败: {str(e)}"}
        )

@app.get("/config/test/{project_name}")
async def test_project_config(project_name: str):
    """测试指定项目的配置"""
    try:
        from config.config import get_bot_for_project, get_lark_config

        # 模拟仓库URL
        repo_url = f"http://example.com/project/{project_name}.git"

        # 获取匹配的机器人
        bot_id = get_bot_for_project(repo_url, project_name)
        bot_config = get_lark_config(bot_id)

        return {
            "status": "success",
            "project_name": project_name,
            "repo_url": repo_url,
            "matched_bot_id": bot_id,
            "bot_config": {
                "name": bot_config["name"],
                "webhook_url": bot_config["webhook_url"][:50] + "..." if len(bot_config["webhook_url"]) > 50 else bot_config["webhook_url"],
                "timeout": bot_config["timeout"],
                "retry_count": bot_config["retry_count"]
            },
            "message": f"项目 {project_name} 将使用机器人: {bot_config['name']}"
        }
    except Exception as e:
        logger.error(f"测试项目配置失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"测试项目配置失败: {str(e)}"}
        )

@app.post("/config/mapping")
async def save_project_mapping(mapping: ProjectMapping):
    """保存项目映射配置"""
    try:
        config_manager = get_config_manager()

        # 如果提供了自定义webhook URL，创建自定义机器人
        bot_id = mapping.bot_id
        if mapping.webhook_url:
            # 检查当前机器人的webhook URL
            bots = config_manager.get_lark_bots()
            current_webhook = bots.get(mapping.bot_id, {}).get("webhook_url", "")

            if mapping.webhook_url != current_webhook:
                # 创建自定义机器人配置
                custom_bot_id = f"custom_{mapping.project_name}"
                custom_bot_config = {
                    "webhook_url": mapping.webhook_url,
                    "name": f"自定义机器人-{mapping.project_name}",
                    "timeout": 10,
                    "retry_count": 3,
                    "is_custom": True
                }
                config_manager.add_bot(custom_bot_id, custom_bot_config)
                bot_id = custom_bot_id

        # 保存项目映射
        success = config_manager.add_project_mapping(mapping.project_name, bot_id, mapping.git_url)

        if success:
            logger.info(f"项目映射已保存: {mapping.project_name} -> {bot_id}")
            return {
                "status": "success",
                "message": f"项目 {mapping.project_name} 的配置已保存",
                "mapping": {
                    "project_name": mapping.project_name,
                    "git_url": mapping.git_url,
                    "bot_id": bot_id,
                    "webhook_url": mapping.webhook_url
                }
            }
        else:
            raise Exception("配置保存失败")

    except Exception as e:
        logger.error(f"保存项目映射失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"保存配置失败: {str(e)}"}
        )

@app.delete("/config/mapping")
async def delete_project_mapping(delete_request: DeleteMapping):
    """删除项目映射配置"""
    try:
        config_manager = get_config_manager()
        success = config_manager.delete_project_mapping(delete_request.pattern)

        if success:
            logger.info(f"项目映射已删除: {delete_request.pattern}")
            return {
                "status": "success",
                "message": f"映射 {delete_request.pattern} 已删除"
            }
        else:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": f"映射 {delete_request.pattern} 不存在"}
            )

    except Exception as e:
        logger.error(f"删除项目映射失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"删除配置失败: {str(e)}"}
        )

@app.get("/config/status")
async def get_config_status():
    """获取配置状态"""
    try:
        config_manager = get_config_manager()
        status = config_manager.get_config_status()

        # 添加配置管理器类型信息
        status["config_manager_type"] = CONFIG_MANAGER_TYPE

        return {
            "status": "success",
            "config_status": status,
            "message": "配置状态获取成功"
        }
    except Exception as e:
        logger.error(f"获取配置状态失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"获取配置状态失败: {str(e)}"}
        )

@app.post("/config/bot/test/{bot_id}")
async def test_bot(bot_id: str):
    """测试机器人连接"""
    try:
        from config.config import get_lark_config
        from src.lark_notification import LarkNotifier

        bot_config = get_lark_config(bot_id)
        notifier = LarkNotifier(bot_config=bot_config)

        # 发送测试消息
        test_message = {
            "msg_type": "text",
            "content": {
                "text": f"🧪 机器人测试消息\n机器人: {bot_config['name']}\n时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }

        success = notifier._send_message(test_message)

        if success:
            return {
                "status": "success",
                "message": f"机器人 {bot_config['name']} 测试成功"
            }
        else:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"机器人 {bot_config['name']} 测试失败"}
            )
    except Exception as e:
        logger.error(f"测试机器人失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"测试机器人失败: {str(e)}"}
        )

@app.post("/config/bot/custom")
async def add_custom_bot(custom_bot: CustomBot):
    """添加自定义机器人"""
    try:
        import uuid

        config_manager = get_config_manager()

        # 生成唯一的机器人ID
        bot_id = f"custom_{uuid.uuid4().hex[:8]}"

        # 构建机器人配置
        bot_config = {
            "name": custom_bot.name,
            "webhook_url": custom_bot.webhook_url,
            "timeout": 10,
            "retry_count": 3,
            "is_custom": True
        }

        # 使用配置管理器添加机器人
        success = config_manager.add_bot(bot_id, bot_config)

        if success:
            return {
                "status": "success",
                "message": f"自定义机器人 {custom_bot.name} 添加成功",
                "bot_id": bot_id,
                "bot_config": {
                    "name": custom_bot.name,
                    "webhook_url": custom_bot.webhook_url
                }
            }
        else:
            raise Exception("添加自定义机器人失败")

    except Exception as e:
        logger.error(f"添加自定义机器人失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"添加自定义机器人失败: {str(e)}"}
        )

@app.post("/config/projects/batch")
async def batch_add_projects(batch_data: BatchProjects):
    """批量添加项目"""
    try:
        config_manager = get_config_manager()

        results = {
            "success": [],
            "failed": [],
            "existing": []
        }

        for project in batch_data.projects:
            project_name = project.get("name", "").strip()
            git_url = project.get("git_url", "").strip()

            if not project_name or not git_url:
                results["failed"].append({
                    "project_name": project_name,
                    "git_url": git_url,
                    "error": "项目名称或Git地址为空"
                })
                continue

            # 检查项目是否已存在
            check_result = config_manager.check_project_exists(project_name)
            if check_result.get("exists"):
                results["existing"].append({
                    "project_name": project_name,
                    "git_url": git_url,
                    "bot_id": check_result.get("bot_id"),
                    "bot_name": check_result.get("bot_name")
                })
                continue

            # 添加项目映射
            success = config_manager.add_project_mapping(project_name, batch_data.default_bot_id, git_url)
            if success:
                results["success"].append({
                    "project_name": project_name,
                    "git_url": git_url,
                    "bot_id": batch_data.default_bot_id
                })
            else:
                results["failed"].append({
                    "project_name": project_name,
                    "git_url": git_url,
                    "error": "添加到数据库失败"
                })

        return {
            "status": "success",
            "message": f"批量添加完成：成功 {len(results['success'])} 个，失败 {len(results['failed'])} 个，已存在 {len(results['existing'])} 个",
            "results": results
        }

    except Exception as e:
        logger.error(f"批量添加项目失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"批量添加项目失败: {str(e)}"}
        )

@app.post("/config/projects/check")
async def check_project_exists(project_data: dict):
    """检查项目是否已存在"""
    try:
        config_manager = get_config_manager()

        project_name = project_data.get("project_name", "").strip()
        if not project_name:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "项目名称不能为空"}
            )

        result = config_manager.check_project_exists(project_name)
        return {
            "status": "success",
            "result": result
        }

    except Exception as e:
        logger.error(f"检查项目失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"检查项目失败: {str(e)}"}
        )

@app.post("/config/admin/action")
async def admin_action(action_data: AdminAction):
    """管理员操作（需要密码验证）"""
    try:
        config_manager = get_config_manager()

        # 验证密码
        if not config_manager.verify_admin_password(action_data.password):
            return JSONResponse(
                status_code=403,
                content={"status": "error", "message": "密码错误，无权限执行此操作"}
            )

        if action_data.action == "update_project":
            # 更新项目配置
            project_name = action_data.data.get("project_name")
            new_bot_id = action_data.data.get("bot_id")

            success = config_manager.add_project_mapping(project_name, new_bot_id)

            if success:
                return {
                    "status": "success",
                    "message": f"项目 {project_name} 配置已更新"
                }
            else:
                raise Exception("更新配置失败")

        elif action_data.action == "delete_custom_bot":
            # 删除自定义机器人
            bot_id = action_data.data.get("bot_id")

            success = config_manager.remove_bot(bot_id)
            if success:
                return {
                    "status": "success",
                    "message": f"自定义机器人 {bot_id} 已删除"
                }
            else:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "只能删除自定义机器人"}
                )
        else:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "不支持的操作类型"}
            )

    except Exception as e:
        logger.error(f"管理员操作失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"操作失败: {str(e)}"}
        )

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
            logger.info(f"   1. 使用命令: python -m uvicorn app:app --host 0.0.0.0 --port 8002")
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
