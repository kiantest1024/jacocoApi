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
from feishu_notification import send_error_notification

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

        # 通知逻辑已移到 run_jacoco_scan_docker 函数中

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
    运行JaCoCo扫描，根据配置选择Docker或本地扫描，并处理通知
    """
    # 执行扫描
    scan_result = None

    # 检查是否强制使用本地扫描
    if service_config.get('force_local_scan', False):
        logger.info(f"[{request_id}] 强制使用本地扫描")
        scan_result = _run_local_scan(repo_url, commit_id, branch_name, reports_dir, service_config, request_id)
    elif service_config.get('use_docker', True):
        # 优先尝试Docker扫描
        logger.info(f"[{request_id}] 优先使用Docker扫描")

        # 检查Docker是否可用
        if _check_docker_available(request_id):
            try:
                scan_result = _run_docker_scan(repo_url, commit_id, branch_name, reports_dir, service_config, request_id)
                logger.info(f"[{request_id}] ✅ Docker扫描成功完成")
            except Exception as docker_error:
                logger.warning(f"[{request_id}] Docker扫描失败，回退到本地扫描: {str(docker_error)}")
                scan_result = _run_local_scan(repo_url, commit_id, branch_name, reports_dir, service_config, request_id)
        else:
            logger.warning(f"[{request_id}] Docker不可用，使用本地扫描")
            scan_result = _run_local_scan(repo_url, commit_id, branch_name, reports_dir, service_config, request_id)
    else:
        logger.info(f"[{request_id}] 配置为使用本地扫描")
        scan_result = _run_local_scan(repo_url, commit_id, branch_name, reports_dir, service_config, request_id)

    # 通知发送由调用方(app.py)统一处理
    scan_result["notification_handled_by_caller"] = True

    return scan_result

def _check_docker_available(request_id: str) -> bool:
    """
    检查Docker是否可用
    """
    try:
        # 检查Docker命令是否存在
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            logger.warning(f"[{request_id}] Docker命令不可用: {result.stderr}")
            return False

        # 检查Docker守护进程是否运行
        result = subprocess.run(
            ['docker', 'info'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            logger.warning(f"[{request_id}] Docker守护进程未运行: {result.stderr}")
            return False

        # 检查Docker镜像是否存在
        docker_image = 'jacoco-scanner:latest'
        result = subprocess.run(
            ['docker', 'images', '-q', docker_image],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0 or not result.stdout.strip():
            logger.warning(f"[{request_id}] Docker镜像 {docker_image} 不存在")
            logger.info(f"[{request_id}] 请先构建Docker镜像: docker build -t {docker_image} -f docker/Dockerfile .")
            return False

        logger.info(f"[{request_id}] ✅ Docker环境检查通过")
        return True

    except subprocess.TimeoutExpired:
        logger.warning(f"[{request_id}] Docker检查超时")
        return False
    except FileNotFoundError:
        logger.warning(f"[{request_id}] Docker命令未找到")
        return False
    except Exception as e:
        logger.warning(f"[{request_id}] Docker检查失败: {str(e)}")
        return False

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

        # 初始化所有覆盖率指标
        counters = {
            "INSTRUCTION": {"missed": 0, "covered": 0},
            "BRANCH": {"missed": 0, "covered": 0},
            "LINE": {"missed": 0, "covered": 0},
            "COMPLEXITY": {"missed": 0, "covered": 0},
            "METHOD": {"missed": 0, "covered": 0},
            "CLASS": {"missed": 0, "covered": 0}
        }

        # 解析所有counter元素
        for counter in root.findall(".//counter"):
            counter_type = counter.get("type")
            missed = int(counter.get("missed", 0))
            covered = int(counter.get("covered", 0))

            if counter_type in counters:
                counters[counter_type]["missed"] += missed
                counters[counter_type]["covered"] += covered

        # 计算各项覆盖率
        def calculate_coverage(counter_data):
            total = counter_data["missed"] + counter_data["covered"]
            return (counter_data["covered"] / total * 100) if total > 0 else 0

        instruction_coverage = calculate_coverage(counters["INSTRUCTION"])
        branch_coverage = calculate_coverage(counters["BRANCH"])
        line_coverage = calculate_coverage(counters["LINE"])
        complexity_coverage = calculate_coverage(counters["COMPLEXITY"])
        method_coverage = calculate_coverage(counters["METHOD"])
        class_coverage = calculate_coverage(counters["CLASS"])

        result = {
            # 主要覆盖率指标
            "coverage_percentage": round(line_coverage, 2),  # 保持向后兼容
            "instruction_coverage": round(instruction_coverage, 2),
            "branch_coverage": round(branch_coverage, 2),
            "line_coverage": round(line_coverage, 2),
            "complexity_coverage": round(complexity_coverage, 2),
            "method_coverage": round(method_coverage, 2),
            "class_coverage": round(class_coverage, 2),

            # 详细统计数据
            "instructions_covered": counters["INSTRUCTION"]["covered"],
            "instructions_total": counters["INSTRUCTION"]["missed"] + counters["INSTRUCTION"]["covered"],
            "branches_covered": counters["BRANCH"]["covered"],
            "branches_total": counters["BRANCH"]["missed"] + counters["BRANCH"]["covered"],
            "lines_covered": counters["LINE"]["covered"],
            "lines_total": counters["LINE"]["missed"] + counters["LINE"]["covered"],
            "complexity_covered": counters["COMPLEXITY"]["covered"],
            "complexity_total": counters["COMPLEXITY"]["missed"] + counters["COMPLEXITY"]["covered"],
            "methods_covered": counters["METHOD"]["covered"],
            "methods_total": counters["METHOD"]["missed"] + counters["METHOD"]["covered"],
            "classes_covered": counters["CLASS"]["covered"],
            "classes_total": counters["CLASS"]["missed"] + counters["CLASS"]["covered"]
        }

        logger.info(f"[{request_id}] JaCoCo XML parsing completed:")
        logger.info(f"[{request_id}]   指令覆盖率: {instruction_coverage:.2f}%")
        logger.info(f"[{request_id}]   分支覆盖率: {branch_coverage:.2f}%")
        logger.info(f"[{request_id}]   行覆盖率: {line_coverage:.2f}%")
        logger.info(f"[{request_id}]   圈复杂度覆盖率: {complexity_coverage:.2f}%")
        logger.info(f"[{request_id}]   方法覆盖率: {method_coverage:.2f}%")
        logger.info(f"[{request_id}]   类覆盖率: {class_coverage:.2f}%")

        return result

    except Exception as e:
        logger.error(f"[{request_id}] Failed to parse JaCoCo XML: {str(e)}")
        raise Exception(f"Failed to parse JaCoCo XML: {str(e)}")

def _run_local_scan(
    repo_url: str,
    commit_id: str,
    branch_name: str,  # 保留以保持接口一致性
    reports_dir: str,
    service_config: Dict[str, Any],  # 保留以保持接口一致性
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

        # 4. 检查项目源代码结构
        logger.info(f"[{request_id}] 检查项目源代码...")
        src_main_java = os.path.join(repo_dir, "src", "main", "java")
        src_test_java = os.path.join(repo_dir, "src", "test", "java")

        has_main_code = False
        has_test_code = False

        if os.path.exists(src_main_java):
            for root, _, files in os.walk(src_main_java):
                if any(f.endswith('.java') for f in files):
                    has_main_code = True
                    break

        if os.path.exists(src_test_java):
            for root, _, files in os.walk(src_test_java):
                if any(f.endswith('.java') for f in files):
                    has_test_code = True
                    break

        logger.info(f"[{request_id}] 源代码检查结果: 主代码={has_main_code}, 测试代码={has_test_code}")

        if not has_main_code:
            logger.warning(f"[{request_id}] 项目没有主代码，将继续扫描但可能没有覆盖率数据")
        if not has_test_code:
            logger.warning(f"[{request_id}] 项目没有测试代码，覆盖率将为0%")

        # 5. 备份并增强pom.xml
        logger.info(f"[{request_id}] 增强pom.xml以支持JaCoCo...")
        pom_backup = os.path.join(repo_dir, "pom.xml.backup")
        shutil.copy2(pom_path, pom_backup)

        try:
            enhance_pom_simple(pom_path, request_id)
        except Exception as e:
            logger.warning(f"[{request_id}] pom.xml增强失败: {str(e)}")
            # 如果增强失败，恢复备份
            try:
                shutil.copy2(pom_backup, pom_path)
                logger.info(f"[{request_id}] 已恢复原始pom.xml")
            except Exception as restore_error:
                logger.error(f"[{request_id}] 恢复pom.xml失败: {restore_error}")

        # 6. 运行Maven测试和JaCoCo
        logger.info(f"[{request_id}] 运行Maven测试和JaCoCo...")

        maven_cmd = [
            "mvn", "clean", "compile", "test-compile", "test",
            "jacoco:report",
            "-Dmaven.test.failure.ignore=true",
            "-Dproject.build.sourceEncoding=UTF-8",
            "-Dmaven.compiler.source=11",
            "-Dmaven.compiler.target=11"
        ]

        result = subprocess.run(
            maven_cmd,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=600
        )

        logger.info(f"[{request_id}] Maven执行完成，返回码: {result.returncode}")
        logger.info(f"[{request_id}] Maven输出:\n{result.stdout}")
        logger.info(f"[{request_id}] Maven错误:\n{result.stderr}")

        # 7. 检查target目录内容
        target_dir = os.path.join(repo_dir, "target")
        if os.path.exists(target_dir):
            logger.info(f"[{request_id}] target目录存在，列出内容...")
            try:
                for root, _, files in os.walk(target_dir):
                    level = root.replace(target_dir, '').count(os.sep)
                    indent = ' ' * 2 * level
                    logger.info(f"[{request_id}] {indent}{os.path.basename(root)}/")
                    subindent = ' ' * 2 * (level + 1)
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        logger.info(f"[{request_id}] {subindent}{file} ({file_size} bytes)")
            except Exception as e:
                logger.warning(f"[{request_id}] 列出target目录失败: {e}")
        else:
            logger.warning(f"[{request_id}] target目录不存在")

        # 8. 查找并复制JaCoCo报告
        logger.info(f"[{request_id}] 查找JaCoCo报告...")

        # 可能的报告位置（按优先级排序）
        possible_locations = [
            os.path.join(repo_dir, "target", "site", "jacoco", "jacoco.xml"),
            os.path.join(repo_dir, "target", "jacoco-reports", "jacoco.xml"),
            os.path.join(repo_dir, "target", "jacoco", "jacoco.xml"),
            os.path.join(repo_dir, "target", "reports", "jacoco", "jacoco.xml")
        ]

        logger.info(f"[{request_id}] 检查可能的报告位置:")
        for location in possible_locations:
            exists = os.path.exists(location)
            logger.info(f"[{request_id}]   {location}: {'✅' if exists else '❌'}")

        jacoco_xml = None
        jacoco_html_dir = None

        # 查找XML报告
        for location in possible_locations:
            if os.path.exists(location):
                jacoco_xml = location
                jacoco_html_dir = os.path.dirname(location)
                logger.info(f"[{request_id}] 找到JaCoCo XML报告: {location}")
                break

        # 如果还没找到，搜索整个target目录
        if not jacoco_xml:
            logger.info(f"[{request_id}] 在target目录中搜索JaCoCo报告...")
            target_dir = os.path.join(repo_dir, "target")
            if os.path.exists(target_dir):
                for root, _, files in os.walk(target_dir):
                    for file in files:
                        if file == "jacoco.xml":
                            jacoco_xml = os.path.join(root, file)
                            jacoco_html_dir = root
                            logger.info(f"[{request_id}] 搜索到JaCoCo XML报告: {jacoco_xml}")
                            break
                    if jacoco_xml:
                        break

        scan_result = {
            "status": "completed" if result.returncode == 0 else "partial",
            "maven_output": result.stdout,
            "maven_errors": result.stderr,
            "return_code": result.returncode,
            "scan_method": "local"
        }

        os.makedirs(reports_dir, exist_ok=True)

        if jacoco_xml and os.path.exists(jacoco_xml):
            logger.info(f"[{request_id}] 找到JaCoCo XML报告: {jacoco_xml}")

            # 复制XML报告到输出目录
            xml_dest = os.path.join(reports_dir, "jacoco.xml")
            shutil.copy2(jacoco_xml, xml_dest)
            logger.info(f"[{request_id}] 复制XML报告到: {xml_dest}")

            # 复制整个JaCoCo HTML目录
            if jacoco_html_dir and os.path.exists(jacoco_html_dir):
                html_output = os.path.join(reports_dir, "html")
                if os.path.exists(html_output):
                    shutil.rmtree(html_output)
                shutil.copytree(jacoco_html_dir, html_output)
                logger.info(f"[{request_id}] 复制完整HTML报告到: {html_output}")

                # 列出复制的文件
                html_files = []
                for root, _, files in os.walk(html_output):
                    for file in files:
                        rel_path = os.path.relpath(os.path.join(root, file), html_output)
                        html_files.append(rel_path)
                logger.info(f"[{request_id}] 复制了 {len(html_files)} 个HTML文件")

            # 复制CSV报告（如果存在）
            csv_path = os.path.join(jacoco_html_dir, "jacoco.csv")
            if os.path.exists(csv_path):
                csv_dest = os.path.join(reports_dir, "jacoco.csv")
                shutil.copy2(csv_path, csv_dest)
                logger.info(f"[{request_id}] 复制CSV报告到: {csv_dest}")

            # 解析报告
            try:
                parsed_reports = parse_jacoco_reports(reports_dir, request_id)
                scan_result.update(parsed_reports)
                logger.info(f"[{request_id}] JaCoCo报告解析成功")

                # 显示覆盖率摘要
                if 'coverage_percentage' in scan_result:
                    logger.info(f"[{request_id}] 覆盖率摘要:")
                    logger.info(f"[{request_id}]   行覆盖率: {scan_result.get('coverage_percentage', 'N/A')}%")
                    logger.info(f"[{request_id}]   分支覆盖率: {scan_result.get('branch_coverage', 'N/A')}%")
                    logger.info(f"[{request_id}]   覆盖行数: {scan_result.get('lines_covered', 'N/A')}/{scan_result.get('lines_total', 'N/A')}")

                    # 创建coverage_summary用于通知
                    scan_result["coverage_summary"] = {
                        "instruction_coverage": scan_result.get('instruction_coverage', 0),
                        "branch_coverage": scan_result.get('branch_coverage', 0),
                        "line_coverage": scan_result.get('line_coverage', 0),
                        "complexity_coverage": scan_result.get('complexity_coverage', 0),
                        "method_coverage": scan_result.get('method_coverage', 0),
                        "class_coverage": scan_result.get('class_coverage', 0)
                    }
                    logger.info(f"[{request_id}] 创建coverage_summary用于通知")

            except Exception as e:
                logger.warning(f"[{request_id}] 解析报告失败: {str(e)}")
                # 即使解析失败，也标记为成功，因为报告文件已生成
                scan_result["status"] = "completed"
                scan_result["message"] = f"报告生成成功，但解析失败: {str(e)}"
        else:
            logger.warning(f"[{request_id}] 未找到JaCoCo XML报告")
            scan_result["status"] = "no_reports"

            # 即使没有报告，也提供基本的覆盖率信息（0%）
            scan_result.update({
                "reports_available": False,
                "xml_report_path": None,
                "html_report_available": False,
                "summary_available": False,
                "coverage_percentage": 0,
                "instruction_coverage": 0,
                "branch_coverage": 0,
                "line_coverage": 0,
                "complexity_coverage": 0,
                "method_coverage": 0,
                "class_coverage": 0,
                "instructions_covered": 0,
                "instructions_total": 0,
                "branches_covered": 0,
                "branches_total": 0,
                "lines_covered": 0,
                "lines_total": 0,
                "complexity_covered": 0,
                "complexity_total": 0,
                "methods_covered": 0,
                "methods_total": 0,
                "classes_covered": 0,
                "classes_total": 0
            })
            logger.info(f"[{request_id}] 设置默认覆盖率数据（0%）")

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

def enhance_pom_simple(pom_path: str, request_id: str) -> bool:
    """
    使用字符串替换简单增强pom.xml
    """
    try:
        import re

        logger.info(f"[{request_id}] 读取pom.xml...")

        # 读取pom.xml
        with open(pom_path, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.info(f"[{request_id}] 原始pom.xml大小: {len(content)} 字符")

        # 检查是否已有JaCoCo插件
        if 'jacoco-maven-plugin' in content:
            logger.info(f"[{request_id}] JaCoCo插件已存在，跳过增强")
            return True

        # 检查并添加JUnit依赖
        if 'junit' not in content.lower():
            logger.info(f"[{request_id}] 添加JUnit依赖...")
            junit_dependency = '''
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>'''

            if '<dependencies>' in content:
                # 在现有dependencies中添加
                content = content.replace(
                    '<dependencies>',
                    f'<dependencies>{junit_dependency}'
                )
                logger.info(f"[{request_id}] 在现有dependencies中添加JUnit")
            else:
                # 创建dependencies节点
                dependencies_block = f'''
    <dependencies>{junit_dependency}
    </dependencies>'''

                # 在</properties>后添加
                if '</properties>' in content:
                    content = content.replace('</properties>', f'</properties>{dependencies_block}')
                else:
                    # 在</version>后添加
                    version_pattern = r'(\s*</version>\s*)'
                    if re.search(version_pattern, content):
                        content = re.sub(version_pattern, r'\1' + dependencies_block, content, count=1)

                logger.info(f"[{request_id}] 创建dependencies节点并添加JUnit")

        # 添加JaCoCo属性
        jacoco_property = '<jacoco.version>0.8.7</jacoco.version>'

        if '<properties>' in content and jacoco_property not in content:
            # 在现有properties中添加
            content = content.replace(
                '<properties>',
                f'<properties>\n        {jacoco_property}'
            )
            logger.info(f"[{request_id}] 在现有properties中添加JaCoCo版本")
        elif '<properties>' not in content:
            # 创建properties节点
            # 在</version>后添加properties
            version_pattern = r'(\s*</version>\s*)'
            if re.search(version_pattern, content):
                properties_block = f'''
    <properties>
        {jacoco_property}
    </properties>'''
                content = re.sub(version_pattern, r'\1' + properties_block, content, count=1)
                logger.info(f"[{request_id}] 创建properties节点并添加JaCoCo版本")

        # 添加JaCoCo插件
        jacoco_plugin = '''
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>${jacoco.version}</version>
                <executions>
                    <execution>
                        <id>prepare-agent</id>
                        <goals>
                            <goal>prepare-agent</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>report</id>
                        <phase>test</phase>
                        <goals>
                            <goal>report</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>'''

        if '<plugins>' in content:
            # 在现有plugins中添加
            content = content.replace(
                '<plugins>',
                f'<plugins>{jacoco_plugin}'
            )
            logger.info(f"[{request_id}] 在现有plugins中添加JaCoCo插件")
        elif '<build>' in content:
            # 在build中创建plugins
            plugins_block = f'''
        <plugins>{jacoco_plugin}
        </plugins>'''
            content = content.replace(
                '<build>',
                f'<build>{plugins_block}'
            )
            logger.info(f"[{request_id}] 在build中创建plugins并添加JaCoCo插件")
        else:
            # 创建完整的build节点
            build_block = f'''
    <build>
        <plugins>{jacoco_plugin}
        </plugins>
    </build>'''
            # 在</dependencies>后或</properties>后添加
            if '</dependencies>' in content:
                content = content.replace('</dependencies>', f'</dependencies>{build_block}')
            elif '</properties>' in content:
                content = content.replace('</properties>', f'</properties>{build_block}')
            else:
                # 在</project>前添加
                content = content.replace('</project>', f'{build_block}\n</project>')
            logger.info(f"[{request_id}] 创建完整的build节点并添加JaCoCo插件")

        # 写回文件
        with open(pom_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"[{request_id}] pom.xml增强完成，新大小: {len(content)} 字符")
        return True

    except Exception as e:
        logger.error(f"[{request_id}] pom.xml增强失败: {e}")
        return False
