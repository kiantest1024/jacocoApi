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
