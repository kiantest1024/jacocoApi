import os
import logging
import subprocess
import tempfile
import shutil
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any
from celery import Celery

from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from feishu_notification import send_jacoco_notification, send_error_notification

logger = logging.getLogger(__name__)

celery_app = Celery(
    'jacoco_tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

@celery_app.task(name='scan_tasks.run_docker_jacoco_scan', bind=True, max_retries=3)
def run_docker_jacoco_scan(
    self,
    repo_url: str,
    commit_id: str,
    branch_name: str,
    service_config: Dict[str, Any],
    request_id: str
) -> Dict[str, Any]:
    reports_dir = None
    try:
        reports_dir = tempfile.mkdtemp(prefix=f"jacoco_reports_{request_id}_")
        logger.info(f"[{request_id}] Using reports directory: {reports_dir}")

        scan_result = run_jacoco_scan_docker(
            repo_url, commit_id, branch_name, reports_dir, service_config, request_id
        )

        report_data = parse_jacoco_reports(reports_dir, request_id)

        final_result = {
            "status": "success",
            "request_id": request_id,
            "repo_url": repo_url,
            "commit_id": commit_id,
            "branch_name": branch_name,
            "service_name": service_config.get('service_name'),
            **scan_result,
            **report_data
        }

        webhook_url = service_config.get('notification_webhook')
        if webhook_url and 'coverage_summary' in report_data:
            try:
                send_jacoco_notification(
                    webhook_url=webhook_url,
                    repo_url=repo_url,
                    branch_name=branch_name,
                    commit_id=commit_id,
                    coverage_data=report_data['coverage_summary'],
                    service_name=service_config.get('service_name')
                )
            except Exception as e:
                logger.warning(f"[{request_id}] Failed to send notification: {str(e)}")

        return final_result

    except Exception as e:
        error_msg = f"JaCoCo scan failed: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}", exc_info=True)
        
        webhook_url = service_config.get('notification_webhook')
        if webhook_url:
            try:
                send_error_notification(
                    webhook_url=webhook_url,
                    repo_url=repo_url,
                    error_message=error_msg,
                    service_name=service_config.get('service_name')
                )
            except Exception as notify_error:
                logger.error(f"[{request_id}] Failed to send error notification: {str(notify_error)}")

        raise self.retry(countdown=60, exc=e)

    finally:
        if reports_dir and os.path.exists(reports_dir):
            try:
                shutil.rmtree(reports_dir)
            except Exception as e:
                logger.warning(f"[{request_id}] Failed to cleanup reports directory: {str(e)}")

def run_jacoco_scan_docker(
    repo_url: str,
    commit_id: str,
    branch_name: str,
    reports_dir: str,
    service_config: Dict[str, Any],
    request_id: str
) -> Dict[str, Any]:
    """
    运行JaCoCo扫描，根据配置选择Docker或本地扫描
    """
    # 检查是否强制使用本地扫描
    if service_config.get('force_local_scan', False) or not service_config.get('use_docker', True):
        logger.info(f"[{request_id}] 配置为使用本地扫描")
        return _run_local_scan(repo_url, commit_id, branch_name, reports_dir, service_config, request_id)

    # 尝试Docker扫描，失败时回退到本地扫描
    try:
        return _run_docker_scan(repo_url, commit_id, branch_name, reports_dir, service_config, request_id)
    except Exception as docker_error:
        logger.warning(f"[{request_id}] Docker扫描失败，尝试本地扫描: {str(docker_error)}")
        return _run_local_scan(repo_url, commit_id, branch_name, reports_dir, service_config, request_id)

def _run_docker_scan(
    repo_url: str,
    commit_id: str,
    branch_name: str,
    reports_dir: str,
    service_config: Dict[str, Any],
    request_id: str
) -> Dict[str, Any]:

    logger.info(f"[{request_id}] Starting Docker JaCoCo scan")
    logger.info(f"[{request_id}] Repository: {repo_url}")
    logger.info(f"[{request_id}] Commit: {commit_id}")
    logger.info(f"[{request_id}] Branch: {branch_name}")

    docker_image = service_config.get('docker_image', 'jacoco-scanner:latest')
    logger.info(f"[{request_id}] Using Docker image: {docker_image}")

    os.makedirs(reports_dir, exist_ok=True)
    abs_reports_dir = os.path.abspath(reports_dir)

    repos_base_dir = "./repos"
    os.makedirs(repos_base_dir, exist_ok=True)
    abs_repos_dir = os.path.abspath(repos_base_dir)

    service_name = service_config.get('service_name', 'project')
    docker_cmd = [
        'docker', 'run', '--rm',
        '-v', f'{abs_reports_dir}:/app/reports',
        '-v', f'{abs_repos_dir}:/app/repos',
        docker_image,
        '/app/scripts/scan.sh',
        '--repo-url', repo_url,
        '--commit-id', commit_id,
        '--branch', branch_name,
        '--service-name', service_name
    ]

    try:
        logger.info(f"[{request_id}] Executing Docker command: {' '.join(docker_cmd)}")
        
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=service_config.get('scan_timeout', 1800)
        )

        if result.returncode == 0:
            logger.info(f"[{request_id}] Docker scan completed successfully")
            
            report_files = []
            if os.path.exists(abs_reports_dir):
                for root, _, files in os.walk(abs_reports_dir):
                    for file in files:
                        if file.endswith(('.xml', '.html', '.json')):
                            report_files.append(os.path.join(root, file))

            if report_files:
                try:
                    parsed_reports = parse_jacoco_reports(abs_reports_dir, request_id)
                    return {
                        "status": "success",
                        "docker_output": result.stdout,
                        "report_files": report_files,
                        **parsed_reports
                    }
                except Exception as e:
                    logger.error(f"[{request_id}] Failed to parse reports: {str(e)}")
                    return {
                        "status": "partial_success",
                        "docker_output": result.stdout,
                        "report_files": report_files,
                        "parse_error": str(e)
                    }
            else:
                logger.warning(f"[{request_id}] No report files generated")
                return {
                    "status": "no_reports",
                    "docker_output": result.stdout,
                    "message": "Docker scan completed but no reports were generated"
                }
        else:
            logger.error(f"[{request_id}] Docker scan failed with return code {result.returncode}")
            logger.error(f"[{request_id}] Docker stderr: {result.stderr}")
            raise Exception(f"Docker scan failed with return code {result.returncode}: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error(f"[{request_id}] Docker scan timed out")
        raise Exception("Docker scan timed out")
    except Exception as e:
        logger.error(f"[{request_id}] Docker scan failed: {str(e)}")
        raise Exception(f"Docker scan failed: {str(e)}")

def parse_jacoco_reports(reports_dir: str, request_id: str) -> Dict[str, Any]:
    logger.info(f"[{request_id}] Parsing JaCoCo reports: {reports_dir}")

    jacoco_xml_path = os.path.join(reports_dir, "jacoco.xml")
    summary_json_path = os.path.join(reports_dir, "summary.json")
    html_report_dir = os.path.join(reports_dir, "html")

    result = {
        "reports_available": False,
        "xml_report_path": None,
        "html_report_available": False,
        "summary_available": False
    }

    if os.path.exists(jacoco_xml_path):
        logger.info(f"[{request_id}] Found JaCoCo XML report")
        result["xml_report_path"] = jacoco_xml_path
        result["reports_available"] = True

        try:
            coverage_data = parse_jacoco_xml_file(jacoco_xml_path, request_id)
            result.update(coverage_data)
        except Exception as e:
            logger.warning(f"[{request_id}] Failed to parse XML report: {str(e)}")
    else:
        logger.warning(f"[{request_id}] JaCoCo XML report not found")

    if os.path.exists(html_report_dir):
        logger.info(f"[{request_id}] Found JaCoCo HTML report")
        result["html_report_available"] = True
        result["html_report_path"] = html_report_dir

    if os.path.exists(summary_json_path):
        try:
            with open(summary_json_path, 'r') as f:
                summary_data = json.load(f)
            result["coverage_summary"] = summary_data
            result["summary_available"] = True
            logger.info(f"[{request_id}] Loaded coverage summary from JSON")
        except Exception as e:
            logger.warning(f"[{request_id}] Failed to load summary JSON: {str(e)}")

    return result

def parse_jacoco_xml_file(xml_path: str, request_id: str) -> Dict[str, Any]:
    try:
        logger.info(f"[{request_id}] Parsing JaCoCo XML file: {xml_path}")
        
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        total_lines = 0
        covered_lines = 0
        total_branches = 0
        covered_branches = 0
        
        for counter in root.findall(".//counter"):
            counter_type = counter.get("type")
            missed = int(counter.get("missed", 0))
            covered = int(counter.get("covered", 0))
            
            if counter_type == "LINE":
                total_lines += missed + covered
                covered_lines += covered
            elif counter_type == "BRANCH":
                total_branches += missed + covered
                covered_branches += covered
        
        line_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        branch_coverage = (covered_branches / total_branches * 100) if total_branches > 0 else 0
        
        result = {
            "coverage_percentage": round(line_coverage, 2),
            "line_coverage": round(line_coverage, 2),
            "branch_coverage": round(branch_coverage, 2),
            "lines_covered": covered_lines,
            "lines_total": total_lines,
            "branches_covered": covered_branches,
            "branches_total": total_branches
        }
        
        logger.info(f"[{request_id}] JaCoCo XML parsing completed - Line coverage: {line_coverage:.2f}%")
        return result
        
    except Exception as e:
        logger.error(f"[{request_id}] Failed to parse JaCoCo XML: {str(e)}")
        raise Exception(f"Failed to parse JaCoCo XML: {str(e)}")

def _run_local_scan(
    repo_url: str,
    commit_id: str,
    branch_name: str,
    reports_dir: str,
    service_config: Dict[str, Any],
    request_id: str
) -> Dict[str, Any]:
    """
    本地JaCoCo扫描（不使用Docker）
    """
    logger.info(f"[{request_id}] 开始本地JaCoCo扫描")

    import tempfile
    import shutil

    # 创建临时工作目录
    temp_dir = tempfile.mkdtemp(prefix=f"jacoco_local_{request_id}_")
    repo_dir = os.path.join(temp_dir, "repo")

    try:
        # 1. 克隆仓库
        logger.info(f"[{request_id}] 克隆仓库到: {repo_dir}")
        clone_cmd = ["git", "clone", repo_url, repo_dir]
        result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            raise Exception(f"克隆仓库失败: {result.stderr}")

        # 2. 切换到指定提交
        logger.info(f"[{request_id}] 切换到提交: {commit_id}")
        checkout_cmd = ["git", "checkout", commit_id]
        result = subprocess.run(checkout_cmd, cwd=repo_dir, capture_output=True, text=True)

        if result.returncode != 0:
            logger.warning(f"[{request_id}] 切换提交失败，使用默认分支: {result.stderr}")

        # 3. 检查是否为Maven项目
        pom_path = os.path.join(repo_dir, "pom.xml")
        if not os.path.exists(pom_path):
            raise Exception("不是Maven项目，未找到pom.xml文件")

        logger.info(f"[{request_id}] 找到Maven项目")

        # 4. 运行Maven测试和JaCoCo
        logger.info(f"[{request_id}] 运行Maven测试和JaCoCo...")

        maven_cmd = [
            "mvn", "clean", "test",
            "org.jacoco:jacoco-maven-plugin:0.8.7:prepare-agent",
            "org.jacoco:jacoco-maven-plugin:0.8.7:report",
            "-Dmaven.test.failure.ignore=true",
            "-Dproject.build.sourceEncoding=UTF-8"
        ]

        result = subprocess.run(
            maven_cmd,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=600
        )

        logger.info(f"[{request_id}] Maven执行完成，返回码: {result.returncode}")

        # 5. 查找并复制JaCoCo报告
        jacoco_xml = os.path.join(repo_dir, "target", "site", "jacoco", "jacoco.xml")
        jacoco_html_dir = os.path.join(repo_dir, "target", "site", "jacoco")

        scan_result = {
            "status": "completed" if result.returncode == 0 else "partial",
            "maven_output": result.stdout,
            "maven_errors": result.stderr,
            "return_code": result.returncode,
            "scan_method": "local"
        }

        os.makedirs(reports_dir, exist_ok=True)

        if os.path.exists(jacoco_xml):
            logger.info(f"[{request_id}] 找到JaCoCo XML报告")

            # 复制报告到输出目录
            shutil.copy2(jacoco_xml, reports_dir)

            if os.path.exists(jacoco_html_dir):
                html_output = os.path.join(reports_dir, "html")
                if os.path.exists(html_output):
                    shutil.rmtree(html_output)
                shutil.copytree(jacoco_html_dir, html_output)
                logger.info(f"[{request_id}] 复制HTML报告到: {html_output}")

            # 解析报告
            try:
                parsed_reports = parse_jacoco_reports(reports_dir, request_id)
                scan_result.update(parsed_reports)
            except Exception as e:
                logger.warning(f"[{request_id}] 解析报告失败: {str(e)}")
        else:
            logger.warning(f"[{request_id}] 未找到JaCoCo报告")
            scan_result["status"] = "no_reports"

        return scan_result

    except subprocess.TimeoutExpired:
        logger.error(f"[{request_id}] 本地扫描超时")
        return {"status": "timeout", "message": "本地扫描超时", "scan_method": "local"}
    except Exception as e:
        logger.error(f"[{request_id}] 本地扫描失败: {str(e)}")
        return {"status": "error", "message": str(e), "scan_method": "local"}
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"[{request_id}] 清理临时目录完成")
        except Exception as cleanup_error:
            logger.warning(f"[{request_id}] 清理失败: {cleanup_error}")
