#!/usr/bin/env python3
"""
JaCoCo API 调试版本
提供详细的扫描日志和构建信息输出
"""

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

# 强制设置环境变量为文件配置，防止 .env 文件覆盖
os.environ['CONFIG_STORAGE_TYPE'] = 'file'
os.environ['JACOCO_DEBUG_MODE'] = 'true'
os.environ['JACOCO_VERBOSE_LOGGING'] = 'true'

try:
    from dotenv import load_dotenv
    load_dotenv()
    # 再次强制设置，确保不被 .env 文件覆盖
    os.environ['CONFIG_STORAGE_TYPE'] = 'file'
    os.environ['JACOCO_DEBUG_MODE'] = 'true'
    os.environ['JACOCO_VERBOSE_LOGGING'] = 'true'
except ImportError:
    pass

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('jacoco_debug.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="JaCoCo Scanner API (Debug Mode)", version="2.0.0-debug")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

templates = Jinja2Templates(directory="static/templates")

# 强制使用文件配置
CONFIG_MANAGER_TYPE = 'file'

def init_config_manager():
    """初始化配置管理器"""
    logger.info("🔧 [DEBUG] 初始化配置管理器...")
    logger.debug(f"[DEBUG] CONFIG_STORAGE_TYPE: {os.environ.get('CONFIG_STORAGE_TYPE')}")
    logger.debug(f"[DEBUG] JACOCO_DEBUG_MODE: {os.environ.get('JACOCO_DEBUG_MODE')}")
    logger.debug(f"[DEBUG] JACOCO_VERBOSE_LOGGING: {os.environ.get('JACOCO_VERBOSE_LOGGING')}")
    logger.info("✅ 使用文件配置管理 (调试模式)")
    return True

# 初始化配置管理器
config_init_success = init_config_manager()

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
    logger.debug("[DEBUG] 获取配置管理器...")
    return FileConfigWrapper()

class FileConfigWrapper:

    def get_lark_bots(self):
        logger.debug("[DEBUG] 获取 Lark 机器人配置...")
        from config.config import list_all_bots
        bots = list_all_bots()
        logger.debug(f"[DEBUG] 找到 {len(bots)} 个机器人配置")
        return bots

    def get_project_mappings(self):
        logger.debug("[DEBUG] 获取项目映射配置...")
        from config.config import list_project_mappings
        mappings = list_project_mappings()
        logger.debug(f"[DEBUG] 找到 {len(mappings)} 个项目映射")
        return mappings

    def add_bot(self, bot_id: str, bot_config: dict) -> bool:
        try:
            logger.debug(f"[DEBUG] 添加机器人: {bot_id}")
            from config import config
            config.LARK_BOTS[bot_id] = bot_config
            logger.info(f"✅ 机器人 {bot_id} 添加成功")
            return True
        except Exception as e:
            logger.error(f"❌ 添加机器人失败: {e}")
            return False

    def remove_bot(self, bot_id: str) -> bool:
        try:
            logger.debug(f"[DEBUG] 删除机器人: {bot_id}")
            from config import config
            if bot_id in config.LARK_BOTS and config.LARK_BOTS[bot_id].get('is_custom', False):
                del config.LARK_BOTS[bot_id]
                logger.info(f"✅ 机器人 {bot_id} 删除成功")
                return True
            logger.warning(f"⚠️  机器人 {bot_id} 不存在或不可删除")
            return False
        except Exception as e:
            logger.error(f"❌ 删除机器人失败: {e}")
            return False

    def add_project_mapping(self, project_name: str, bot_id: str, git_url: str = None) -> bool:
        try:
            logger.debug(f"[DEBUG] 添加项目映射: {project_name} -> {bot_id}")
            from config import config
            config.PROJECT_BOT_MAPPING[project_name] = bot_id
            logger.info(f"✅ 项目映射 {project_name} 添加成功")
            return True
        except Exception as e:
            logger.error(f"❌ 添加项目映射失败: {e}")
            return False

    def delete_project_mapping(self, project_name: str) -> bool:
        try:
            logger.debug(f"[DEBUG] 删除项目映射: {project_name}")
            from config import config
            if project_name in config.PROJECT_BOT_MAPPING:
                del config.PROJECT_BOT_MAPPING[project_name]
                logger.info(f"✅ 项目映射 {project_name} 删除成功")
                return True
            logger.warning(f"⚠️  项目映射 {project_name} 不存在")
            return False
        except Exception as e:
            logger.error(f"❌ 删除项目映射失败: {e}")
            return False

    def check_project_exists(self, project_name: str) -> dict:
        try:
            logger.debug(f"[DEBUG] 检查项目是否存在: {project_name}")
            from config.config import check_project_exists
            result = check_project_exists(project_name)
            logger.debug(f"[DEBUG] 项目检查结果: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ 检查项目失败: {e}")
            return {"exists": False}

    def verify_admin_password(self, password: str) -> bool:
        try:
            logger.debug("[DEBUG] 验证管理员密码...")
            from config.config import verify_admin_password
            result = verify_admin_password(password)
            logger.debug(f"[DEBUG] 密码验证结果: {'通过' if result else '失败'}")
            return result
        except Exception as e:
            logger.error(f"❌ 密码验证失败: {e}")
            return False

    def get_config_status(self) -> dict:
        try:
            logger.debug("[DEBUG] 获取配置状态...")
            from config.config import list_all_bots, list_project_mappings
            bots = list_all_bots()
            mappings = list_project_mappings()
            status = {
                "storage_type": "File (Debug Mode)",
                "total_bots": len(bots),
                "total_mappings": len(mappings),
                "custom_bots": sum(1 for bot in bots.values() if bot.get('is_custom', False)),
                "environment": "Debug",
                "persistent": False,
                "debug_mode": True,
                "verbose_logging": True
            }
            logger.debug(f"[DEBUG] 配置状态: {status}")
            return status
        except Exception as e:
            logger.error(f"❌ 获取配置状态失败: {e}")
            return {"error": str(e)}

def get_service_config(repo_url: str) -> Dict[str, Any]:
    logger.debug(f"[DEBUG] 获取服务配置: {repo_url}")
    from config.config import get_service_config as config_get_service_config
    config = config_get_service_config(repo_url)
    
    # 在调试模式下启用详细日志
    config.update({
        "debug_mode": True,
        "verbose_logging": True
    })
    
    logger.debug(f"[DEBUG] 服务配置: {config}")
    return config

def get_server_base_url(request: Request = None) -> str:
    if request:
        host = request.headers.get("host", "localhost:8002")
        scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
        url = f"{scheme}://{host}"
        logger.debug(f"[DEBUG] 服务器基础URL: {url}")
        return url
    return "http://localhost:8002"

def save_html_report(reports_dir: str, project_name: str, commit_id: str, request_id: str, base_url: str = None) -> str:
    try:
        logger.debug(f"[{request_id}] [DEBUG] 保存HTML报告...")
        logger.debug(f"[{request_id}] [DEBUG] 源目录: {reports_dir}")
        logger.debug(f"[{request_id}] [DEBUG] 项目名: {project_name}")
        logger.debug(f"[{request_id}] [DEBUG] 提交ID: {commit_id}")
        
        import shutil
        project_reports_dir = os.path.join(REPORTS_BASE_DIR, project_name)
        os.makedirs(project_reports_dir, exist_ok=True)
        logger.debug(f"[{request_id}] [DEBUG] 项目报告目录: {project_reports_dir}")

        source_html_dir = os.path.join(reports_dir, "html")
        if not os.path.exists(source_html_dir):
            logger.warning(f"[{request_id}] ⚠️  HTML报告目录不存在: {source_html_dir}")
            return None

        target_html_dir = os.path.join(project_reports_dir, commit_id[:8])
        if os.path.exists(target_html_dir):
            logger.debug(f"[{request_id}] [DEBUG] 删除旧报告目录: {target_html_dir}")
            shutil.rmtree(target_html_dir)

        logger.debug(f"[{request_id}] [DEBUG] 复制报告: {source_html_dir} -> {target_html_dir}")
        shutil.copytree(source_html_dir, target_html_dir)
        
        relative_url = f"/reports/{project_name}/{commit_id[:8]}/index.html"
        full_url = f"{base_url}{relative_url}" if base_url else relative_url

        logger.info(f"[{request_id}] ✅ HTML报告已保存: {target_html_dir}")
        logger.debug(f"[{request_id}] [DEBUG] 报告URL: {full_url}")
        return full_url
    except Exception as e:
        logger.error(f"[{request_id}] ❌ 保存HTML报告失败: {str(e)}")
        return None

@app.get("/")
async def root():
    logger.debug("[DEBUG] 访问根路径")
    return {
        "message": "JaCoCo Scanner API (Debug Mode)",
        "version": "2.0.0-debug",
        "docs": "/docs",
        "config": "/config",
        "debug_mode": True,
        "log_file": "jacoco_debug.log"
    }

@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    logger.debug("[DEBUG] 访问配置页面")
    return templates.TemplateResponse("config.html", {"request": request})

@app.get("/health")
async def health_check():
    logger.debug("[DEBUG] 健康检查")
    return {
        "status": "healthy",
        "version": "2.0.0-debug",
        "service": "JaCoCo Scanner (Debug Mode)",
        "debug_mode": True,
        "timestamp": time.time()
    }

@app.get("/debug/logs")
async def get_debug_logs():
    """获取调试日志"""
    try:
        logger.debug("[DEBUG] 获取调试日志...")
        if os.path.exists('jacoco_debug.log'):
            with open('jacoco_debug.log', 'r', encoding='utf-8') as f:
                logs = f.readlines()
                # 返回最后100行日志
                return {
                    "status": "success",
                    "logs": logs[-100:],
                    "total_lines": len(logs),
                    "message": "最近100行调试日志"
                }
        else:
            return {
                "status": "warning",
                "logs": [],
                "message": "调试日志文件不存在"
            }
    except Exception as e:
        logger.error(f"❌ 获取调试日志失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"获取日志失败: {str(e)}"}
        )

@app.post("/github/webhook-no-auth")
def github_webhook_no_auth_debug(request: Request):
    """调试版本的Webhook处理器"""
    try:
        request_id = f"debug_req_{int(time.time())}"
        logger.info(f"[{request_id}] 🔍 [DEBUG] 收到Webhook请求（调试模式）")

        import asyncio
        try:
            loop = asyncio.get_running_loop()
            body = loop.run_until_complete(request.body())
        except RuntimeError:
            body = asyncio.run(request.body())

        if not body:
            raise HTTPException(status_code=400, detail="Empty request body")

        payload = json.loads(body)
        logger.debug(f"[{request_id}] [DEBUG] Webhook载荷: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        event_type = "unknown"
        repo_url = None
        commit_id = None
        branch_name = "main"

        # 解析Webhook载荷
        if "object_kind" in payload:
            event_type = "gitlab_push"
            logger.debug(f"[{request_id}] [DEBUG] 检测到GitLab推送事件")

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
            logger.debug(f"[{request_id}] [DEBUG] 检测到GitHub推送事件")
            repo_url = payload.get("repository", {}).get("clone_url")
            commit_id = payload.get("after", "unknown")
            ref = payload.get("ref", "refs/heads/main")
            branch_name = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else "main"

        if not repo_url:
            raise HTTPException(status_code=400, detail="Cannot extract repository URL from webhook")

        logger.debug(f"[{request_id}] [DEBUG] 解析结果:")
        logger.debug(f"[{request_id}] [DEBUG]   事件类型: {event_type}")
        logger.debug(f"[{request_id}] [DEBUG]   仓库URL: {repo_url}")
        logger.debug(f"[{request_id}] [DEBUG]   提交ID: {commit_id}")
        logger.debug(f"[{request_id}] [DEBUG]   分支名: {branch_name}")

        service_config = get_service_config(repo_url)
        service_name = service_config['service_name']

        # 调试模式强制使用较短超时
        service_config.update({
            'debug_mode': True,
            'debug_timeout': 180,  # 调试模式3分钟超时
            'scan_timeout': 180,   # 强制短超时
            'verbose_logging': True
        })

        logger.info(f"[{request_id}] 🎯 开始调试扫描...")
        logger.info(f"[{request_id}] 📋 项目: {service_name}")
        logger.info(f"[{request_id}] 🔗 仓库: {repo_url}")
        logger.info(f"[{request_id}] 📝 提交: {commit_id}")
        logger.info(f"[{request_id}] 🌿 分支: {branch_name}")

        try:
            from src.jacoco_tasks_debug import run_jacoco_scan_docker_debug, parse_jacoco_reports_debug
            import tempfile

            reports_dir = tempfile.mkdtemp(prefix=f"jacoco_debug_reports_{request_id}_")
            logger.debug(f"[{request_id}] [DEBUG] 报告目录: {reports_dir}")

            # 使用调试版本的扫描函数
            scan_result = run_jacoco_scan_docker_debug(
                repo_url, commit_id, branch_name, reports_dir, service_config, request_id
            )

            logger.debug(f"[{request_id}] [DEBUG] 扫描结果: {scan_result}")

            report_data = parse_jacoco_reports_debug(reports_dir, request_id)
            logger.debug(f"[{request_id}] [DEBUG] 报告数据: {report_data}")

            base_url = get_server_base_url(request)
            html_report_url = save_html_report(reports_dir, service_name, commit_id, request_id, base_url)

            if html_report_url:
                report_data['html_report_url'] = html_report_url
                logger.info(f"[{request_id}] 🔗 HTML报告链接: {html_report_url}")

            # 发送 Lark 机器人通知
            notification_result = None
            try:
                logger.info(f"[{request_id}] 📤 发送 Lark 机器人通知...")

                # 导入通知模块
                from src.lark_notification import send_jacoco_notification

                # 准备通知数据
                notification_data = {
                    "service_name": service_name,
                    "commit_id": commit_id,
                    "branch_name": branch_name,
                    "repo_url": repo_url,
                    "coverage_data": report_data.get("coverage_summary", {}),
                    "html_report_url": html_report_url,
                    "scan_method": scan_result.get("method", "unknown"),
                    "request_id": request_id
                }

                # 获取配置管理器
                config_manager = get_config_manager()

                # 发送通知
                success = send_jacoco_notification(
                    repo_url=repo_url,
                    branch_name=branch_name,
                    commit_id=commit_id,
                    coverage_data=report_data.get("coverage_summary", {}),
                    scan_result=scan_result,
                    request_id=request_id,
                    html_report_url=html_report_url,
                    bot_id="default"
                )

                notification_result = {
                    "success": success,
                    "message": "Lark 通知发送成功" if success else "Lark 通知发送失败"
                }

                if notification_result and notification_result.get("success"):
                    logger.info(f"[{request_id}] ✅ Lark 通知发送成功")
                else:
                    logger.warning(f"[{request_id}] ⚠️  Lark 通知发送失败: {notification_result}")

            except ImportError as import_error:
                logger.error(f"[{request_id}] ❌ Lark 通知模块导入失败: {import_error}")
                notification_result = {"success": False, "error": f"通知模块导入失败: {str(import_error)}"}
            except Exception as notification_error:
                logger.error(f"[{request_id}] ❌ Lark 通知发送异常: {notification_error}")
                notification_result = {"success": False, "error": str(notification_error)}

            # 构建详细的调试响应
            response_data = {
                "status": "completed",
                "request_id": request_id,
                "event_type": event_type,
                "message": f"调试扫描完成 - 项目: {service_name}, 提交: {commit_id[:8]}",
                "debug_info": {
                    "scan_method": scan_result.get("method", "unknown"),
                    "scan_analysis": scan_result.get("analysis", {}),
                    "service_config": service_config,
                    "reports_dir": reports_dir,
                    "notification_result": notification_result
                },
                "scan_result": scan_result,
                "report_data": report_data,
                "notification_result": notification_result,
                "extracted_info": {
                    "repo_url": repo_url,
                    "commit_id": commit_id,
                    "branch_name": branch_name,
                    "service_name": service_name
                }
            }

            logger.info(f"[{request_id}] ✅ 调试扫描完成")
            logger.debug(f"[{request_id}] [DEBUG] 完整响应: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

            return JSONResponse(
                status_code=200,
                content=response_data
            )

        except Exception as sync_error:
            logger.error(f"[{request_id}] ❌ 调试扫描失败: {sync_error}")
            import traceback
            logger.error(f"[{request_id}] 📋 错误堆栈: {traceback.format_exc()}")

            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "request_id": request_id,
                    "message": f"调试扫描失败: {str(sync_error)}",
                    "error_details": str(sync_error),
                    "error_traceback": traceback.format_exc(),
                    "extracted_info": {
                        "repo_url": repo_url,
                        "commit_id": commit_id,
                        "branch_name": branch_name,
                        "service_name": service_name
                    }
                }
            )

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"[{request_id}] ❌ Webhook处理失败: {str(e)}")
        import traceback
        logger.error(f"[{request_id}] 📋 错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

@app.get("/config/bots")
async def get_lark_bots():
    """获取 Lark 机器人配置"""
    try:
        config_manager = get_config_manager()
        bots = config_manager.get_lark_bots()
        return bots
    except Exception as e:
        logger.error(f"获取机器人配置失败: {e}")
        return {}

@app.get("/config/mappings")
async def get_project_mappings():
    """获取项目映射配置"""
    try:
        config_manager = get_config_manager()
        mappings = config_manager.get_project_mappings()
        return mappings
    except Exception as e:
        logger.error(f"获取项目映射失败: {e}")
        return []

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting JaCoCo Scanner API (Debug Mode)...")
    logger.info("📡 Server: http://localhost:8003 (Debug Port)")   
    logger.info("📖 Docs: http://localhost:8003/docs")
    logger.info("🔍 Debug Logs: http://localhost:8003/debug/logs")
    logger.info("📄 Log File: jacoco_debug.log")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8003, log_level="debug")
    except KeyboardInterrupt:
        logger.info("🔚 调试服务已关闭")
    except Exception as e:
        logger.error(f"❌ 启动调试服务失败: {e}")
