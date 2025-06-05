import os
import logging
import subprocess
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any

logger = logging.getLogger(__name__)

def run_jacoco_scan_docker(
    repo_url: str,
    commit_id: str,
    branch_name: str,
    reports_dir: str,
    service_config: Dict[str, Any],
    request_id: str
) -> Dict[str, Any]:
    # 优先尝试Docker扫描
    if _check_docker_available(request_id):
        try:
            logger.info(f"[{request_id}] 使用Docker扫描")
            scan_result = _run_docker_scan(repo_url, commit_id, branch_name, reports_dir, service_config, request_id)
            scan_result["notification_handled_by_caller"] = True
            return scan_result
        except Exception as e:
            logger.warning(f"[{request_id}] Docker扫描失败，回退到本地扫描: {str(e)}")

    # 回退到本地扫描
    logger.info(f"[{request_id}] 使用本地扫描")
    scan_result = _run_local_scan(repo_url, commit_id, branch_name, reports_dir, service_config, request_id)
    scan_result["notification_handled_by_caller"] = True
    return scan_result

def _check_docker_available(request_id: str) -> bool:
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return False

        result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return False

        # 检查或构建镜像
        image_name = 'jacoco-scanner:latest'
        result = subprocess.run(['docker', 'images', '-q', image_name], capture_output=True, text=True, timeout=5)
        if not result.stdout.strip():
            logger.info(f"[{request_id}] 构建JaCoCo Docker镜像...")
            build_result = subprocess.run(['docker', 'build', '-t', image_name, '.'],
                                        capture_output=True, text=True, timeout=300)
            if build_result.returncode != 0:
                logger.warning(f"[{request_id}] Docker镜像构建失败: {build_result.stderr}")
                return False

        logger.info(f"[{request_id}] Docker环境可用")
        return True
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
    logger.info(f"[{request_id}] 开始Docker JaCoCo扫描")

    os.makedirs(reports_dir, exist_ok=True)
    abs_reports_dir = os.path.abspath(reports_dir)
    service_name = service_config.get('service_name', 'project')

    docker_cmd = [
        'docker', 'run', '--rm',
        '-v', f'{abs_reports_dir}:/app/reports',
        'jacoco-scanner:latest',
        '--repo-url', repo_url,
        '--commit-id', commit_id,
        '--branch', branch_name,
        '--service-name', service_name
    ]

    try:
        logger.info(f"[{request_id}] 执行Docker命令: {' '.join(docker_cmd)}")
        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            logger.info(f"[{request_id}] Docker扫描成功")
            return {
                "status": "completed",
                "scan_method": "docker",
                "docker_output": result.stdout,
                "return_code": result.returncode
            }
        else:
            logger.error(f"[{request_id}] Docker扫描失败: {result.stderr}")
            raise Exception(f"Docker扫描失败: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error(f"[{request_id}] Docker扫描超时")
        raise Exception("Docker扫描超时")
    except Exception as e:
        logger.error(f"[{request_id}] Docker扫描异常: {str(e)}")
        raise e

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

            result["coverage_summary"] = {
                "instruction_coverage": coverage_data.get('instruction_coverage', 0),
                "branch_coverage": coverage_data.get('branch_coverage', 0),
                "line_coverage": coverage_data.get('line_coverage', 0),
                "complexity_coverage": coverage_data.get('complexity_coverage', 0),
                "method_coverage": coverage_data.get('method_coverage', 0),
                "class_coverage": coverage_data.get('class_coverage', 0)
            }

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

        counters = {
            "INSTRUCTION": {"missed": 0, "covered": 0},
            "BRANCH": {"missed": 0, "covered": 0},
            "LINE": {"missed": 0, "covered": 0},
            "COMPLEXITY": {"missed": 0, "covered": 0},
            "METHOD": {"missed": 0, "covered": 0},
            "CLASS": {"missed": 0, "covered": 0}
        }

        for counter in root.findall(".//counter"):
            counter_type = counter.get("type")
            missed = int(counter.get("missed", 0))
            covered = int(counter.get("covered", 0))

            if counter_type in counters:
                counters[counter_type]["missed"] += missed
                counters[counter_type]["covered"] += covered

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
            "coverage_percentage": round(line_coverage, 2),
            "instruction_coverage": round(instruction_coverage, 2),
            "branch_coverage": round(branch_coverage, 2),
            "line_coverage": round(line_coverage, 2),
            "complexity_coverage": round(complexity_coverage, 2),
            "method_coverage": round(method_coverage, 2),
            "class_coverage": round(class_coverage, 2),
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
    _: str,  # branch_name
    reports_dir: str,
    __: Dict[str, Any],  # service_config
    request_id: str
) -> Dict[str, Any]:
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
        main_java_files = []
        test_java_files = []

        # 检查主代码
        if os.path.exists(src_main_java):
            for root, _, files in os.walk(src_main_java):
                for file in files:
                    if file.endswith('.java'):
                        main_java_files.append(os.path.join(root, file))
                        has_main_code = True

        # 检查测试代码
        if os.path.exists(src_test_java):
            for root, _, files in os.walk(src_test_java):
                for file in files:
                    if file.endswith('.java'):
                        test_java_files.append(os.path.join(root, file))
                        has_test_code = True

        logger.info(f"[{request_id}] 源代码检查结果: 主代码={has_main_code}, 测试代码={has_test_code}")
        logger.info(f"[{request_id}] 主代码文件数: {len(main_java_files)}")
        logger.info(f"[{request_id}] 测试代码文件数: {len(test_java_files)}")

        # 显示找到的文件（前3个）
        if main_java_files:
            sample_main = [os.path.relpath(f, repo_dir) for f in main_java_files[:3]]
            logger.info(f"[{request_id}] 主代码示例: {sample_main}")
        if test_java_files:
            sample_test = [os.path.relpath(f, repo_dir) for f in test_java_files[:3]]
            logger.info(f"[{request_id}] 测试代码示例: {sample_test}")

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

        # 首先尝试离线模式，如果失败则使用在线模式
        logger.info(f"[{request_id}] 执行JaCoCo扫描（优化版本）")

        # 离线模式命令
        maven_cmd_offline = [
            "mvn", "clean", "compile", "test-compile", "test",
            "jacoco:report",
            "-Dmaven.test.failure.ignore=true",
            "-Dproject.build.sourceEncoding=UTF-8",
            "-Dmaven.compiler.source=11",
            "-Dmaven.compiler.target=11",
            "-o",  # 离线模式
            "--batch-mode"
        ]

        # 在线模式命令（备用）
        maven_cmd_online = [
            "mvn", "clean", "compile", "test-compile", "test",
            "jacoco:report",
            "-Dmaven.test.failure.ignore=true",
            "-Dproject.build.sourceEncoding=UTF-8",
            "-Dmaven.compiler.source=11",
            "-Dmaven.compiler.target=11",
            "--batch-mode",
            "-Dmaven.wagon.http.retryHandler.count=2"
        ]

        # 先尝试离线模式
        logger.info(f"[{request_id}] 尝试离线模式扫描...")
        result = subprocess.run(
            maven_cmd_offline,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=300  # 离线模式应该很快
        )

        # 如果离线模式失败，使用在线模式
        if result.returncode != 0:
            logger.warning(f"[{request_id}] 离线模式失败，切换到在线模式...")
            result = subprocess.run(
                maven_cmd_online,
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=600  # 在线模式允许更长时间
            )

        logger.info(f"[{request_id}] Maven执行完成，返回码: {result.returncode}")
        logger.info(f"[{request_id}] Maven输出:\n{result.stdout}")
        logger.info(f"[{request_id}] Maven错误:\n{result.stderr}")

        # 检查是否是依赖解析问题并尝试回退方案
        if result.returncode != 0 and "Non-resolvable parent POM" in result.stdout:
            logger.warning(f"[{request_id}] 检测到父POM解析问题，尝试创建独立pom.xml...")

            # 创建独立的pom.xml，不依赖父POM
            try:
                independent_pom_content = create_independent_pom(repo_dir, request_id)
                if independent_pom_content:
                    # 备份原始pom.xml
                    original_pom = os.path.join(repo_dir, "pom.xml")
                    backup_pom = os.path.join(repo_dir, "pom.xml.backup")
                    shutil.copy2(original_pom, backup_pom)

                    # 写入独立pom.xml
                    with open(original_pom, 'w', encoding='utf-8') as f:
                        f.write(independent_pom_content)

                    logger.info(f"[{request_id}] 创建独立pom.xml成功，重新尝试Maven扫描...")

                    # 使用独立pom.xml重新扫描 - 简化版本
                    maven_cmd_independent = [
                        "mvn", "clean", "compile", "test-compile", "test",
                        "jacoco:report",
                        "-Dmaven.test.failure.ignore=true",
                        "-Dproject.build.sourceEncoding=UTF-8",
                        "-Dmaven.compiler.source=11",
                        "-Dmaven.compiler.target=11",
                        "-Dcheckstyle.skip=true",
                        "-Dpmd.skip=true",
                        "-Dspotbugs.skip=true"
                    ]

                    result_independent = subprocess.run(
                        maven_cmd_independent,
                        cwd=repo_dir,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )

                    logger.info(f"[{request_id}] 独立pom.xml扫描完成，返回码: {result_independent.returncode}")
                    if result_independent.returncode == 0:
                        logger.info(f"[{request_id}] 独立pom.xml扫描成功")
                        result = result_independent  # 使用独立扫描的结果

                        # 如果没有源代码但Maven成功，创建基本的JaCoCo报告
                        target_dir = os.path.join(repo_dir, "target")
                        if not os.path.exists(target_dir):
                            logger.info(f"[{request_id}] 项目无源代码，创建基本JaCoCo报告...")
                            create_basic_jacoco_report(repo_dir, request_id)
                    else:
                        logger.warning(f"[{request_id}] 独立pom.xml扫描也失败: {result_independent.stdout}")

                    # 恢复原始pom.xml
                    shutil.copy2(backup_pom, original_pom)
                    os.remove(backup_pom)

            except Exception as e:
                logger.warning(f"[{request_id}] 独立pom.xml方案异常: {e}")

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

def create_basic_jacoco_report(repo_dir: str, request_id: str):
    """
    为没有源代码的项目创建基本的JaCoCo报告
    """
    try:
        # 创建target目录结构
        target_dir = os.path.join(repo_dir, "target")
        jacoco_dir = os.path.join(target_dir, "site", "jacoco")
        os.makedirs(jacoco_dir, exist_ok=True)

        # 创建基本的jacoco.xml报告
        jacoco_xml_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!DOCTYPE report PUBLIC "-//JACOCO//DTD Report 1.1//EN" "report.dtd">
<report name="No Source Code Project">
    <sessioninfo id="no-source" start="0" dump="0"/>
    <counter type="INSTRUCTION" missed="0" covered="0"/>
    <counter type="BRANCH" missed="0" covered="0"/>
    <counter type="LINE" missed="0" covered="0"/>
    <counter type="COMPLEXITY" missed="0" covered="0"/>
    <counter type="METHOD" missed="0" covered="0"/>
    <counter type="CLASS" missed="0" covered="0"/>
</report>'''

        jacoco_xml_path = os.path.join(jacoco_dir, "jacoco.xml")
        with open(jacoco_xml_path, 'w', encoding='utf-8') as f:
            f.write(jacoco_xml_content)

        # 创建基本的HTML报告
        html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>JaCoCo Coverage Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }
        .info { margin: 20px 0; padding: 15px; background-color: #e7f3ff; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>JaCoCo Coverage Report</h1>
        <p>Generated for project with no source code</p>
    </div>
    <div class="info">
        <h2>Project Information</h2>
        <p><strong>Status:</strong> No Java source code found</p>
        <p><strong>Coverage:</strong> 0% (No code to analyze)</p>
        <p><strong>Note:</strong> This project appears to be a configuration or documentation project without Java source code.</p>
    </div>
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f0f0f0;">
            <th>Element</th>
            <th>Missed Instructions</th>
            <th>Cov.</th>
            <th>Missed Branches</th>
            <th>Cov.</th>
            <th>Missed</th>
            <th>Cxty</th>
            <th>Missed</th>
            <th>Lines</th>
            <th>Missed</th>
            <th>Methods</th>
            <th>Missed</th>
            <th>Classes</th>
        </tr>
        <tr>
            <td>Total</td>
            <td>0</td>
            <td>n/a</td>
            <td>0</td>
            <td>n/a</td>
            <td>0</td>
            <td>0</td>
            <td>0</td>
            <td>0</td>
            <td>0</td>
            <td>0</td>
            <td>0</td>
            <td>0</td>
        </tr>
    </table>
</body>
</html>'''

        html_path = os.path.join(jacoco_dir, "index.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"[{request_id}] 创建基本JaCoCo报告成功: {jacoco_xml_path}")

    except Exception as e:
        logger.error(f"[{request_id}] 创建基本JaCoCo报告失败: {e}")

def create_independent_pom(repo_dir: str, request_id: str) -> str:
    """
    创建独立的pom.xml，不依赖父POM
    """
    try:
        # 读取原始pom.xml获取基本信息
        original_pom = os.path.join(repo_dir, "pom.xml")
        with open(original_pom, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # 提取项目基本信息
        import re

        # 提取groupId, artifactId, version
        group_match = re.search(r'<groupId>([^<]+)</groupId>', original_content)
        artifact_match = re.search(r'<artifactId>([^<]+)</artifactId>', original_content)
        version_match = re.search(r'<version>([^<]+)</version>', original_content)

        group_id = group_match.group(1) if group_match else "com.example"
        artifact_id = artifact_match.group(1) if artifact_match else "test-project"
        version = version_match.group(1) if version_match else "1.0.0"

        logger.info(f"[{request_id}] 提取项目信息: {group_id}:{artifact_id}:{version}")

        # 创建独立的pom.xml
        independent_pom = f'''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>{group_id}</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>{version}</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <jacoco.version>0.8.7</jacoco.version>
    </properties>

    <dependencies>
        <!-- JUnit for testing -->
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <!-- Maven Compiler Plugin -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.8.1</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                </configuration>
            </plugin>

            <!-- JaCoCo Plugin - 简化配置 -->
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>${{jacoco.version}}</version>
                <executions>
                    <execution>
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
            </plugin>

            <!-- Surefire Plugin for running tests - 简化配置 -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.0.0-M5</version>
                <configuration>
                    <testFailureIgnore>true</testFailureIgnore>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>'''

        logger.info(f"[{request_id}] 创建独立pom.xml成功")
        return independent_pom

    except Exception as e:
        logger.error(f"[{request_id}] 创建独立pom.xml失败: {e}")
        return None

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
