"""
JaCoCo 专用扫描任务模块。
处理 JaCoCo 覆盖率扫描的具体实现。
"""

import os
import logging
import subprocess
import tempfile
import shutil
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from pathlib import Path
from celery import Celery
from celery.signals import task_failure, task_success

from config import settings, CELERY_BROKER_URL, CELERY_RESULT_BACKEND

# 设置日志记录器
logger = logging.getLogger(__name__)

# 初始化 Celery 应用
celery_app = Celery(
    'jacoco_tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)


@celery_app.task(name='scan_tasks.execute_jacoco_scan', bind=True, max_retries=3)
def execute_jacoco_scan(
    self,
    repo_url: str,
    commit_id: str,
    branch_name: str,
    service_config: Dict[str, Any],
    request_id: str = "unknown",
    event_type: str = "push"
) -> Dict[str, Any]:
    """
    使用 Docker 容器执行 JaCoCo 覆盖率扫描。

    参数:
        repo_url: 仓库 URL
        commit_id: 提交 ID
        branch_name: 分支名称
        service_config: 服务配置
        request_id: 请求 ID
        event_type: 事件类型

    返回:
        扫描结果字典
    """
    logger.info(f"[{request_id}] 开始 JaCoCo Docker 扫描 - {service_config['service_name']} - 提交 {commit_id[:8]}")

    reports_dir = None
    try:
        # 创建报告目录
        reports_dir = tempfile.mkdtemp(prefix=f"jacoco_reports_{request_id}_")
        logger.info(f"[{request_id}] 使用报告目录: {reports_dir}")

        # 使用 Docker 执行扫描
        scan_result = run_jacoco_scan_docker(
            repo_url, commit_id, branch_name, reports_dir, service_config, request_id
        )

        # 解析报告
        report_data = parse_jacoco_reports(reports_dir, request_id)

        # 合并结果
        final_result = {
            **scan_result,
            **report_data,
            "service_name": service_config['service_name'],
            "commit_id": commit_id,
            "branch_name": branch_name,
            "event_type": event_type,
            "request_id": request_id
        }

        logger.info(f"[{request_id}] JaCoCo 扫描完成 - 覆盖率: {final_result.get('coverage_percentage', 0):.2f}%")
        return final_result

    except Exception as e:
        logger.error(f"[{request_id}] JaCoCo 扫描失败: {str(e)}", exc_info=True)

        # 重试逻辑
        if self.request.retries < self.max_retries:
            retry_countdown = 60 * (2 ** self.request.retries)
            logger.info(f"[{request_id}] 将在 {retry_countdown} 秒后重试")
            self.retry(exc=e, countdown=retry_countdown)

        return {
            "status": "failed",
            "error": str(e),
            "service_name": service_config.get('service_name', 'unknown'),
            "commit_id": commit_id,
            "branch_name": branch_name,
            "request_id": request_id
        }

    finally:
        # 清理报告目录
        if reports_dir and os.path.exists(reports_dir):
            try:
                shutil.rmtree(reports_dir)
                logger.info(f"[{request_id}] 已清理报告目录: {reports_dir}")
            except Exception as e:
                logger.warning(f"[{request_id}] 清理报告目录失败: {str(e)}")


def run_jacoco_scan_docker(
    repo_url: str,
    commit_id: str,
    branch_name: str,
    reports_dir: str,
    service_config: Dict[str, Any],
    request_id: str
) -> Dict[str, Any]:
    """
    使用 Docker 容器运行 JaCoCo 扫描。

    参数:
        repo_url: 仓库 URL
        commit_id: 提交 ID
        branch_name: 分支名称
        reports_dir: 报告输出目录
        service_config: 服务配置
        request_id: 请求 ID

    返回:
        扫描结果字典
    """
    logger.info(f"[{request_id}] 开始 Docker JaCoCo 扫描")
    logger.info(f"[{request_id}] 仓库: {repo_url}")
    logger.info(f"[{request_id}] 提交: {commit_id}")
    logger.info(f"[{request_id}] 分支: {branch_name}")

    # Docker 镜像名称
    docker_image = service_config.get('docker_image', 'jacoco-scanner:latest')
    logger.info(f"[{request_id}] 使用 Docker 镜像: {docker_image}")

    # 确保报告目录存在
    os.makedirs(reports_dir, exist_ok=True)
    abs_reports_dir = os.path.abspath(reports_dir)
    logger.info(f"[{request_id}] 报告目录: {abs_reports_dir}")

    # 构建 Docker 运行命令
    docker_cmd = [
        'docker', 'run', '--rm',
        '-v', f'{abs_reports_dir}:/app/reports',
        docker_image,
        '/app/scripts/scan.sh',
        '--repo-url', repo_url,
        '--commit-id', commit_id,
        '--branch', branch_name
    ]

    try:
        logger.info(f"[{request_id}] 执行 Docker 命令: {' '.join(docker_cmd)}")

        # 运行 Docker 容器
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=1800  # 30分钟超时
        )

        logger.info(f"[{request_id}] Docker 容器退出，返回码: {result.returncode}")
        logger.info(f"[{request_id}] Docker 标准输出: {result.stdout}")

        if result.stderr:
            logger.warning(f"[{request_id}] Docker 标准错误: {result.stderr}")

        if result.returncode == 0:
            logger.info(f"[{request_id}] Docker 扫描成功完成")

            # 检查报告文件是否生成
            report_files = []
            if os.path.exists(abs_reports_dir):
                for root, dirs, files in os.walk(abs_reports_dir):
                    for file in files:
                        if file.endswith(('.xml', '.html', '.json')):
                            report_files.append(os.path.join(root, file))

            logger.info(f"[{request_id}] 找到报告文件: {report_files}")

            # 解析生成的报告
            if report_files:
                try:
                    parsed_reports = parse_jacoco_reports(abs_reports_dir, request_id)
                    return {
                        "status": "success",
                        "docker_output": result.stdout,
                        "scan_method": "docker",
                        "reports_dir": abs_reports_dir,
                        **parsed_reports
                    }
                except Exception as e:
                    logger.warning(f"[{request_id}] 解析报告失败: {str(e)}")
                    return {
                        "status": "success",
                        "docker_output": result.stdout,
                        "scan_method": "docker",
                        "reports_dir": abs_reports_dir,
                        "report_files": report_files,
                        "parse_error": str(e)
                    }
            else:
                logger.warning(f"[{request_id}] 未找到 JaCoCo 报告文件")
                return {
                    "status": "success",
                    "docker_output": result.stdout,
                    "scan_method": "docker",
                    "reports_dir": abs_reports_dir,
                    "warning": "未找到 JaCoCo 报告文件"
                }
        else:
            logger.error(f"[{request_id}] Docker 扫描失败")
            return {
                "status": "failed",
                "error": result.stderr,
                "docker_output": result.stdout,
                "scan_method": "docker",
                "return_code": result.returncode
            }

    except subprocess.TimeoutExpired:
        logger.error(f"[{request_id}] Docker 扫描超时")
        raise Exception("Docker 扫描超时")
    except Exception as e:
        logger.error(f"[{request_id}] Docker 扫描异常: {str(e)}")
        raise Exception(f"Docker 扫描失败: {str(e)}")


def parse_jacoco_reports(reports_dir: str, request_id: str) -> Dict[str, Any]:
    """
    解析 JaCoCo 报告文件。

    参数:
        reports_dir: 报告目录
        request_id: 请求 ID

    返回:
        解析的报告数据
    """
    logger.info(f"[{request_id}] 解析 JaCoCo 报告: {reports_dir}")

    # 检查报告文件
    jacoco_xml_path = os.path.join(reports_dir, "jacoco.xml")
    summary_json_path = os.path.join(reports_dir, "summary.json")
    html_report_dir = os.path.join(reports_dir, "html")

    result = {
        "reports_available": False,
        "xml_report_path": None,
        "html_report_path": None,
        "summary_data": None
    }

    # 检查 XML 报告
    if os.path.exists(jacoco_xml_path):
        logger.info(f"[{request_id}] 找到 JaCoCo XML 报告")
        result["xml_report_path"] = jacoco_xml_path
        result["reports_available"] = True

        # 解析 XML 报告
        try:
            coverage_data = parse_jacoco_xml_file(jacoco_xml_path, request_id)
            result.update(coverage_data)
        except Exception as e:
            logger.warning(f"[{request_id}] 解析 XML 报告失败: {str(e)}")

    # 检查 HTML 报告
    if os.path.exists(html_report_dir):
        logger.info(f"[{request_id}] 找到 JaCoCo HTML 报告")
        result["html_report_path"] = html_report_dir

    # 检查摘要 JSON
    if os.path.exists(summary_json_path):
        logger.info(f"[{request_id}] 找到报告摘要")
        try:
            with open(summary_json_path, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
                result["summary_data"] = summary_data

                # 从摘要中提取覆盖率信息
                if "coverage" in summary_data:
                    coverage = summary_data["coverage"]
                    if "line" in coverage:
                        result["coverage_percentage"] = coverage["line"]["percentage"]
                        result["lines_covered"] = coverage["line"]["covered"]
                        result["lines_total"] = coverage["line"]["total"]
                    if "branch" in coverage:
                        result["branch_coverage"] = coverage["branch"]["percentage"]
                        result["branches_covered"] = coverage["branch"]["covered"]
                        result["branches_total"] = coverage["branch"]["total"]
        except Exception as e:
            logger.warning(f"[{request_id}] 读取摘要文件失败: {str(e)}")

    if not result["reports_available"]:
        logger.error(f"[{request_id}] 未找到任何 JaCoCo 报告文件")
        raise Exception("未找到 JaCoCo 报告文件")

    return result


def parse_jacoco_xml_file(xml_path: str, request_id: str) -> Dict[str, Any]:
    """
    解析 JaCoCo XML 文件。

    参数:
        xml_path: XML 文件路径
        request_id: 请求 ID

    返回:
        覆盖率数据字典
    """
    try:
        logger.info(f"[{request_id}] 解析 JaCoCo XML 文件: {xml_path}")

        tree = ET.parse(xml_path)
        root = tree.getroot()

        # 提取总体覆盖率信息
        total_lines = 0
        covered_lines = 0
        total_branches = 0
        covered_branches = 0

        # 遍历所有计数器
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

        # 计算覆盖率百分比
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

        logger.info(f"[{request_id}] XML 解析完成 - 行覆盖率: {line_coverage:.2f}%")
        return result

    except Exception as e:
        logger.error(f"[{request_id}] 解析 JaCoCo XML 失败: {str(e)}")
        raise Exception(f"解析 JaCoCo XML 失败: {str(e)}")


def clone_repository(repo_url: str, commit_id: str, branch_name: str, temp_dir: str, request_id: str) -> str:
    """
    克隆 Git 仓库到指定目录。
    
    参数:
        repo_url: 仓库 URL
        commit_id: 提交 ID
        branch_name: 分支名称
        temp_dir: 临时目录
        request_id: 请求 ID
        
    返回:
        克隆的仓库路径
    """
    repo_path = os.path.join(temp_dir, "repo")
    
    try:
        logger.info(f"[{request_id}] 克隆仓库: {repo_url}")
        
        # 克隆仓库
        subprocess.run([
            "git", "clone", "--depth", "1", "--branch", branch_name, repo_url, repo_path
        ], check=True, capture_output=True, text=True)
        
        # 切换到指定提交
        subprocess.run([
            "git", "checkout", commit_id
        ], cwd=repo_path, check=True, capture_output=True, text=True)
        
        logger.info(f"[{request_id}] 仓库克隆成功: {repo_path}")
        return repo_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"[{request_id}] Git 操作失败: {e.stderr}")
        raise Exception(f"Git 操作失败: {e.stderr}")


def run_jacoco_scan(repo_path: str, service_config: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    运行 JaCoCo 扫描。
    
    参数:
        repo_path: 仓库路径
        service_config: 服务配置
        request_id: 请求 ID
        
    返回:
        扫描结果字典
    """
    try:
        logger.info(f"[{request_id}] 开始运行 JaCoCo 扫描")
        
        # 检查是否为 Maven 项目
        pom_file = os.path.join(repo_path, "pom.xml")
        if not os.path.exists(pom_file):
            raise Exception("未找到 pom.xml 文件，不是 Maven 项目")
        
        # 运行 Maven 测试和 JaCoCo 报告
        logger.info(f"[{request_id}] 运行 Maven 测试")
        result = subprocess.run([
            "mvn", "clean", "test", "jacoco:report"
        ], cwd=repo_path, capture_output=True, text=True, timeout=1800)  # 30分钟超时
        
        if result.returncode != 0:
            logger.warning(f"[{request_id}] Maven 测试可能有失败，但继续处理报告")
            logger.warning(f"[{request_id}] Maven 输出: {result.stdout}")
            logger.warning(f"[{request_id}] Maven 错误: {result.stderr}")
        
        # 查找 JaCoCo 报告文件
        jacoco_xml_path = os.path.join(repo_path, "target", "site", "jacoco", "jacoco.xml")
        if not os.path.exists(jacoco_xml_path):
            logger.warning(f"[{request_id}] 未找到 JaCoCo XML 报告，尝试其他位置")
            # 尝试其他可能的位置
            alternative_paths = [
                os.path.join(repo_path, "target", "jacoco-report", "jacoco.xml"),
                os.path.join(repo_path, "target", "jacoco.xml")
            ]
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    jacoco_xml_path = alt_path
                    break
            else:
                raise Exception("未找到 JaCoCo XML 报告文件")
        
        # 解析 JaCoCo 报告
        coverage_data = parse_jacoco_xml(jacoco_xml_path, request_id)
        
        logger.info(f"[{request_id}] JaCoCo 扫描完成")
        return {
            "status": "success",
            "jacoco_xml_path": jacoco_xml_path,
            **coverage_data
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"[{request_id}] Maven 执行超时")
        raise Exception("Maven 执行超时")
    except Exception as e:
        logger.error(f"[{request_id}] JaCoCo 扫描失败: {str(e)}")
        raise


def parse_jacoco_xml(xml_path: str, request_id: str) -> Dict[str, Any]:
    """
    解析 JaCoCo XML 报告。
    
    参数:
        xml_path: JaCoCo XML 文件路径
        request_id: 请求 ID
        
    返回:
        覆盖率数据字典
    """
    try:
        logger.info(f"[{request_id}] 解析 JaCoCo XML 报告: {xml_path}")
        
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 提取总体覆盖率信息
        total_lines = 0
        covered_lines = 0
        total_branches = 0
        covered_branches = 0
        
        # 遍历所有计数器
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
        
        # 计算覆盖率百分比
        line_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        branch_coverage = (covered_branches / total_branches * 100) if total_branches > 0 else 0
        
        # 提取包级别的覆盖率信息
        packages = []
        for package in root.findall("package"):
            package_name = package.get("name", "default")
            package_data = {"name": package_name}
            
            for counter in package.findall("counter"):
                counter_type = counter.get("type")
                missed = int(counter.get("missed", 0))
                covered = int(counter.get("covered", 0))
                total = missed + covered
                
                if counter_type == "LINE":
                    package_data["line_coverage"] = (covered / total * 100) if total > 0 else 0
                    package_data["lines_covered"] = covered
                    package_data["lines_total"] = total
            
            packages.append(package_data)
        
        result = {
            "coverage_percentage": round(line_coverage, 2),
            "line_coverage": round(line_coverage, 2),
            "branch_coverage": round(branch_coverage, 2),
            "lines_covered": covered_lines,
            "lines_total": total_lines,
            "branches_covered": covered_branches,
            "branches_total": total_branches,
            "packages": packages
        }
        
        logger.info(f"[{request_id}] JaCoCo 报告解析完成 - 行覆盖率: {line_coverage:.2f}%")
        return result
        
    except Exception as e:
        logger.error(f"[{request_id}] 解析 JaCoCo XML 失败: {str(e)}")
        raise Exception(f"解析 JaCoCo XML 失败: {str(e)}")


def generate_jacoco_report(repo_path: str, scan_result: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    生成 JaCoCo 报告的额外信息。
    
    参数:
        repo_path: 仓库路径
        scan_result: 扫描结果
        request_id: 请求 ID
        
    返回:
        报告数据字典
    """
    try:
        # 查找 HTML 报告
        html_report_dir = os.path.join(repo_path, "target", "site", "jacoco")
        html_report_path = os.path.join(html_report_dir, "index.html")
        
        report_data = {
            "html_report_available": os.path.exists(html_report_path),
            "html_report_path": html_report_path if os.path.exists(html_report_path) else None
        }
        
        # 如果有 HTML 报告，可以添加更多信息
        if report_data["html_report_available"]:
            logger.info(f"[{request_id}] HTML 报告可用: {html_report_path}")
        
        return report_data
        
    except Exception as e:
        logger.warning(f"[{request_id}] 生成报告信息时出错: {str(e)}")
        return {"html_report_available": False}
