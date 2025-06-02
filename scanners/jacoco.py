"""
JaCoCo 扫描器策略实现。
"""

import os
import subprocess
import shutil
import xml.etree.ElementTree as ET
import time
import logging
import docker
from typing import Dict, Any, List

from .base import BaseScannerStrategy

logger = logging.getLogger(__name__)


class JaCoCoScannerStrategy(BaseScannerStrategy):
    """
    JaCoCo 扫描器策略实现。
    使用 Docker 容器执行 JaCoCo 代码覆盖率扫描。
    """

    def scan(self, repo_url: str, commit_id: str, branch_name: str,
             service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 JaCoCo 执行代码覆盖率扫描。

        参数:
            repo_url: 仓库 URL
            commit_id: 要扫描的提交 ID
            branch_name: 分支名称
            service_config: 服务配置字典

        返回:
            包含扫描结果的字典
        """
        # 1. 获取服务名称
        service_name = service_config.get('service_name', 'unknown')

        # 2. 创建工作目录
        timestamp = int(time.time())
        work_dir = f"/tmp/scan_work_{service_name}_{commit_id[:8]}_{timestamp}"

        try:
            # 确保工作目录存在
            os.makedirs(work_dir, exist_ok=True)

            # 3. 创建子目录
            code_dir = os.path.join(work_dir, "code")
            report_dir = os.path.join(work_dir, "coverage-report")
            os.makedirs(code_dir, exist_ok=True)
            os.makedirs(report_dir, exist_ok=True)

            # 4. 代码更新 - 克隆仓库
            logger.info(f"正在克隆仓库 {repo_url} 的 {branch_name} 分支或提交 {commit_id}")

            # 尝试使用 --depth 1 加速克隆
            clone_success = False
            for attempt in range(3):  # 重试3次
                try:
                    if branch_name and branch_name != "HEAD":
                        clone_cmd = [
                            "git", "clone", "--depth", "1", "--branch", branch_name,
                            repo_url, code_dir
                        ]
                    else:
                        # 如果没有分支名，先克隆再检出
                        clone_cmd = ["git", "clone", "--depth", "1", repo_url, code_dir]

                    subprocess.run(
                        clone_cmd,
                        check=True,
                        capture_output=True
                    )

                    # 如果指定了提交ID且不是分支头部，则检出该提交
                    if commit_id and (not branch_name or commit_id != "HEAD"):
                        subprocess.run(
                            ["git", "checkout", commit_id],
                            check=True,
                            capture_output=True,
                            cwd=code_dir
                        )

                    clone_success = True
                    break
                except subprocess.CalledProcessError as e:
                    logger.warning(f"克隆尝试 {attempt+1} 失败: {e.stderr.decode('utf-8')}")
                    if os.path.exists(code_dir):
                        shutil.rmtree(code_dir)
                        os.makedirs(code_dir, exist_ok=True)
                    time.sleep(5)  # 等待5秒后重试

            if not clone_success:
                return {
                    "status": "error",
                    "message": f"无法克隆仓库 {repo_url} 或检出提交 {commit_id}"
                }

            # 5. 复制 JaCoCo 配置文件
            jacoco_settings_path = os.path.join(work_dir, "jacoco-settings.xml")
            source_settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                               "jacoco-settings.xml")

            if os.path.exists(source_settings_path):
                shutil.copy(source_settings_path, jacoco_settings_path)
            else:
                logger.warning(f"JaCoCo 设置文件不存在: {source_settings_path}")
                return {
                    "status": "error",
                    "message": "JaCoCo 设置文件不存在"
                }

            # 6. 执行 Docker 扫描
            docker_image = service_config.get('docker_image', 'jacoco-scanner-ci')

            # 检查 Docker 是否可用
            try:
                client = docker.from_env()
                # 检查镜像是否存在
                try:
                    client.images.get(docker_image)
                except docker.errors.ImageNotFound:
                    logger.warning(f"Docker 镜像 {docker_image} 不存在，尝试拉取或构建")
                    # 如果镜像不存在，可以尝试构建
                    dockerfile_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                  "jacoco-scanner")
                    if os.path.exists(dockerfile_path):
                        logger.info(f"正在构建 Docker 镜像 {docker_image}")
                        try:
                            # 复制 jacoco-settings.xml 到 Dockerfile 目录
                            shutil.copy(source_settings_path, os.path.join(dockerfile_path, "jacoco-settings.xml"))

                            # 确保 pom.xml 存在
                            pom_path = os.path.join(dockerfile_path, "pom.xml")
                            if not os.path.exists(pom_path):
                                logger.warning(f"pom.xml 不存在: {pom_path}")
                                return {
                                    "status": "error",
                                    "message": "pom.xml 文件不存在"
                                }

                            # 构建镜像
                            client.images.build(
                                path=dockerfile_path,
                                tag=docker_image,
                                rm=True
                            )
                        except Exception as e:
                            logger.error(f"构建 Docker 镜像失败: {str(e)}")
                            return {
                                "status": "error",
                                "message": f"构建 Docker 镜像失败: {str(e)}"
                            }
                    else:
                        return {
                            "status": "error",
                            "message": f"Docker 镜像 {docker_image} 不存在且无法构建"
                        }

                # 运行 Docker 容器
                logger.info(f"正在运行 Docker 容器执行 JaCoCo 扫描")

                # 设置卷挂载
                volumes = {
                    code_dir: {'bind': '/app/code', 'mode': 'ro'},
                    jacoco_settings_path: {'bind': '/app/jacoco-settings.xml', 'mode': 'ro'},
                    report_dir: {'bind': '/app/target/site/jacoco', 'mode': 'rw'}
                }

                # 设置工作目录和命令
                working_dir = '/app/code'
                command = [
                    'mvn', 'clean', 'verify',
                    '-s', '/app/jacoco-settings.xml',
                    '-f', '/app/pom.xml',
                    '-Pcoverage-profile',
                    '-Djacoco.outputDirectory=/app/target/site/jacoco'
                ]

                # 如果配置了增量构建，添加相应参数
                if service_config.get('incremental_build', True):
                    # 获取变更的模块
                    changed_modules = self._get_changed_modules(code_dir, commit_id)
                    if changed_modules:
                        modules_param = ','.join(changed_modules)
                        command.extend(['-pl', modules_param, '-am'])

                # 运行容器
                container = client.containers.run(
                    docker_image,
                    command=command,
                    volumes=volumes,
                    working_dir=working_dir,
                    remove=True,
                    detach=True
                )

                # 获取容器日志
                for log in container.logs(stream=True):
                    logger.debug(log.decode('utf-8').strip())

                # 等待容器完成
                result = container.wait()
                exit_code = result.get('StatusCode', -1)

                if exit_code != 0:
                    logger.error(f"Docker 容器执行失败，退出代码: {exit_code}")
                    return {
                        "status": "error",
                        "message": f"Docker 容器执行失败，退出代码: {exit_code}"
                    }

            except Exception as e:
                logger.error(f"Docker 执行失败: {str(e)}")
                # 如果 Docker 不可用，尝试使用本地 Maven 执行
                return self._fallback_local_scan(code_dir, jacoco_settings_path, report_dir, service_config)

            # 7. 处理扫描结果
            report_path = os.path.join(report_dir, "jacoco.xml")

            if os.path.exists(report_path):
                results = self.parse_results(report_path)
                results["status"] = "success"

                # 8. 保存报告文件路径，以便后续处理
                results["report_path"] = report_path
                results["report_dir"] = report_dir

                return results
            else:
                logger.error(f"JaCoCo 报告文件未生成: {report_path}")
                return {
                    "status": "error",
                    "message": "JaCoCo 报告文件未生成"
                }

        except Exception as e:
            logger.exception(f"扫描过程中出现异常: {str(e)}")
            return {
                "status": "error",
                "message": f"扫描过程中出现异常: {str(e)}"
            }

        finally:
            # 10. 清理工作空间（可选，根据配置决定是否保留）
            if not service_config.get('keep_workspace', False):
                logger.info(f"正在清理工作目录: {work_dir}")
                try:
                    shutil.rmtree(work_dir)
                except Exception as e:
                    logger.warning(f"清理工作目录失败: {str(e)}")

    def _get_changed_modules(self, repo_dir: str, commit_id: str) -> List[str]:
        """
        获取指定提交中变更的模块。

        参数:
            repo_dir: 仓库目录
            commit_id: 提交 ID

        返回:
            变更的模块列表
        """
        try:
            # 获取上一个提交
            result = subprocess.run(
                ["git", "rev-parse", f"{commit_id}^"],
                check=True,
                capture_output=True,
                cwd=repo_dir,
                text=True
            )
            previous_commit = result.stdout.strip()

            # 获取变更的文件
            result = subprocess.run(
                ["git", "diff", "--name-only", previous_commit, commit_id],
                check=True,
                capture_output=True,
                cwd=repo_dir,
                text=True
            )
            changed_files = result.stdout.strip().split('\n')

            # 查找包含 pom.xml 的目录
            modules = set()
            for file_path in changed_files:
                if not file_path:
                    continue

                # 获取文件所在的目录
                dir_path = os.path.dirname(file_path)

                # 向上查找直到找到包含 pom.xml 的目录
                current_dir = dir_path
                while current_dir:
                    pom_path = os.path.join(repo_dir, current_dir, "pom.xml")
                    if os.path.exists(pom_path):
                        modules.add(current_dir if current_dir else '.')
                        break

                    # 向上一级目录
                    parent_dir = os.path.dirname(current_dir)
                    if parent_dir == current_dir:
                        break
                    current_dir = parent_dir

            return list(modules)

        except Exception as e:
            logger.warning(f"获取变更模块失败: {str(e)}")
            return []

    def _fallback_local_scan(self, code_dir: str, jacoco_settings_path: str,
                            report_dir: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        当 Docker 不可用时，使用本地 Maven 执行扫描的回退方法。

        参数:
            code_dir: 代码目录
            jacoco_settings_path: JaCoCo 设置文件路径
            report_dir: 报告目录
            service_config: 服务配置字典

        返回:
            包含扫描结果的字典
        """
        logger.info("Docker 不可用，使用本地 Maven 执行扫描")

        try:
            # 构建 Maven 命令
            maven_cmd = [
                "mvn", "clean", "verify",
                "-s", jacoco_settings_path,
                "-Pcoverage-profile",
                f"-Djacoco.outputDirectory={report_dir}"
            ]

            # 如果配置了增量构建，添加相应参数
            if service_config.get('incremental_build', True):
                # 获取变更的模块
                changed_modules = self._get_changed_modules(code_dir, "HEAD")
                if changed_modules:
                    modules_param = ','.join(changed_modules)
                    maven_cmd.extend(["-pl", modules_param, "-am"])

            # 执行 Maven 命令
            subprocess.run(
                maven_cmd,
                check=True,
                cwd=code_dir
            )

            # 检查报告文件
            report_path = os.path.join(report_dir, "jacoco.xml")

            if os.path.exists(report_path):
                results = self.parse_results(report_path)
                results["status"] = "success"
                results["report_path"] = report_path
                results["report_dir"] = report_dir
                return results
            else:
                return {
                    "status": "error",
                    "message": "JaCoCo 报告文件未生成"
                }

        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"Maven 执行失败: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"本地扫描失败: {str(e)}"
            }

    def parse_results(self, results_path: str) -> Dict[str, Any]:
        """
        解析 JaCoCo XML 报告文件。

        参数:
            results_path: JaCoCo XML 报告文件的路径

        返回:
            包含解析结果的字典
        """
        try:
            tree = ET.parse(results_path)
            root = tree.getroot()

            # 获取总体覆盖率数据
            counter_elements = root.findall(".//counter")

            # 初始化计数器
            counters = {
                "INSTRUCTION": (0, 0),
                "BRANCH": (0, 0),
                "LINE": (0, 0),
                "COMPLEXITY": (0, 0),
                "METHOD": (0, 0),
                "CLASS": (0, 0)
            }

            # 累加计数器
            for counter in counter_elements:
                counter_type = counter.get("type")
                if counter_type in counters:
                    covered = int(counter.get("covered", "0"))
                    missed = int(counter.get("missed", "0"))
                    current_covered, current_missed = counters[counter_type]
                    counters[counter_type] = (current_covered + covered, current_missed + missed)

            # 计算覆盖率百分比
            coverage_percentages = {}
            for counter_type, (covered, missed) in counters.items():
                total = covered + missed
                percentage = (covered / total * 100) if total > 0 else 0
                coverage_percentages[counter_type.lower() + "_coverage"] = round(percentage, 2)

            # 获取行覆盖率详细信息
            line_covered, line_missed = counters["LINE"]
            line_total = line_covered + line_missed

            # 构建结果字典
            result = {
                "coverage_percentage": coverage_percentages.get("line_coverage", 0),
                "lines_covered": line_covered,
                "lines_total": line_total,
                "detailed_coverage": coverage_percentages
            }

            return result

        except Exception as e:
            return {
                "status": "error",
                "message": f"解析 JaCoCo 报告时出错: {str(e)}",
                "coverage_percentage": 0,
                "lines_covered": 0,
                "lines_total": 0
            }
