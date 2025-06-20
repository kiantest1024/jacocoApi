#!/usr/bin/env python3
"""
JaCoCo 任务模块 - 调试版本
提供详细的构建和扫描日志输出
"""

import os
import subprocess
import tempfile
import shutil
import time
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

def _log_command_output(command: str, result: subprocess.CompletedProcess, request_id: str, step: str):
    """记录命令执行的详细输出"""
    logger.info(f"[{request_id}] 🔧 [{step}] 执行命令: {command}")
    logger.debug(f"[{request_id}] [DEBUG] 返回码: {result.returncode}")
    
    if result.stdout:
        logger.info(f"[{request_id}] 📤 [{step}] 标准输出:")
        for line in result.stdout.split('\n'):
            if line.strip():
                logger.info(f"[{request_id}] STDOUT: {line}")
    
    if result.stderr:
        logger.warning(f"[{request_id}] 📥 [{step}] 标准错误:")
        for line in result.stderr.split('\n'):
            if line.strip():
                logger.warning(f"[{request_id}] STDERR: {line}")

def _check_docker_available(request_id: str) -> bool:
    """检查Docker是否可用（调试版本）"""
    logger.debug(f"[{request_id}] [DEBUG] 检查Docker环境...")
    
    try:
        # 检查Docker版本
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
        _log_command_output('docker --version', result, request_id, 'Docker版本检查')
        
        if result.returncode != 0:
            logger.error(f"[{request_id}] ❌ Docker版本检查失败")
            return False

        # 检查Docker服务状态
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=5)
        _log_command_output('docker info', result, request_id, 'Docker服务检查')
        
        if result.returncode != 0:
            logger.error(f"[{request_id}] ❌ Docker服务不可用")
            return False

        # 检查JaCoCo镜像
        image_name = 'jacoco-scanner:latest'
        result = subprocess.run(['docker', 'images', '-q', image_name], capture_output=True, text=True, timeout=5)
        _log_command_output(f'docker images -q {image_name}', result, request_id, 'Docker镜像检查')

        if not result.stdout.strip():
            logger.warning(f"[{request_id}] ⚠️  Docker镜像不存在，将使用本地扫描")
            return False

        logger.info(f"[{request_id}] ✅ Docker环境可用")
        return True

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.error(f"[{request_id}] ❌ Docker检查异常: {e}")
        return False

def _run_maven_command(command: List[str], cwd: str, request_id: str, step: str, timeout: int = 600) -> subprocess.CompletedProcess:
    """运行Maven命令并记录详细输出"""
    cmd_str = ' '.join(command)
    logger.info(f"[{request_id}] 🔨 [{step}] 开始执行Maven命令...")
    logger.debug(f"[{request_id}] [DEBUG] 工作目录: {cwd}")
    logger.debug(f"[{request_id}] [DEBUG] 命令: {cmd_str}")
    logger.debug(f"[{request_id}] [DEBUG] 超时时间: {timeout}秒")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"[{request_id}] ⏱️  [{step}] 执行时间: {duration:.2f}秒")
        _log_command_output(cmd_str, result, request_id, step)
        
        if result.returncode == 0:
            logger.info(f"[{request_id}] ✅ [{step}] 执行成功")
        else:
            logger.error(f"[{request_id}] ❌ [{step}] 执行失败，返回码: {result.returncode}")
        
        return result
        
    except subprocess.TimeoutExpired:
        logger.error(f"[{request_id}] ⏰ [{step}] 命令执行超时 ({timeout}秒)")
        raise
    except Exception as e:
        logger.error(f"[{request_id}] 💥 [{step}] 命令执行异常: {e}")
        raise

def _analyze_maven_output(output: str, request_id: str) -> Dict[str, Any]:
    """分析Maven输出，提取关键信息"""
    logger.debug(f"[{request_id}] [DEBUG] 分析Maven输出...")
    
    analysis = {
        "tests_run": 0,
        "tests_failed": 0,
        "tests_errors": 0,
        "tests_skipped": 0,
        "compilation_errors": [],
        "test_failures": [],
        "jacoco_info": [],
        "build_warnings": []
    }
    
    lines = output.split('\n')
    for line in lines:
        line = line.strip()
        
        # 测试结果统计
        if "Tests run:" in line:
            logger.debug(f"[{request_id}] [DEBUG] 发现测试结果行: {line}")
            try:
                parts = line.split(',')
                for part in parts:
                    part = part.strip()
                    if part.startswith("Tests run:"):
                        analysis["tests_run"] = int(part.split(':')[1].strip())
                    elif part.startswith("Failures:"):
                        analysis["tests_failed"] = int(part.split(':')[1].strip())
                    elif part.startswith("Errors:"):
                        analysis["tests_errors"] = int(part.split(':')[1].strip())
                    elif part.startswith("Skipped:"):
                        analysis["tests_skipped"] = int(part.split(':')[1].strip())
            except (ValueError, IndexError) as e:
                logger.warning(f"[{request_id}] ⚠️  解析测试结果失败: {e}")
        
        # 编译错误
        elif "[ERROR]" in line and ("COMPILATION ERROR" in line or "cannot find symbol" in line):
            analysis["compilation_errors"].append(line)
            logger.warning(f"[{request_id}] 🔴 编译错误: {line}")
        
        # 测试失败
        elif "[ERROR]" in line and ("FAILED" in line or "AssertionError" in line):
            analysis["test_failures"].append(line)
            logger.warning(f"[{request_id}] 🔴 测试失败: {line}")
        
        # JaCoCo信息
        elif "jacoco" in line.lower() or "coverage" in line.lower():
            analysis["jacoco_info"].append(line)
            logger.debug(f"[{request_id}] [DEBUG] JaCoCo信息: {line}")
        
        # 构建警告
        elif "[WARNING]" in line:
            analysis["build_warnings"].append(line)
            logger.debug(f"[{request_id}] [DEBUG] 构建警告: {line}")
    
    logger.info(f"[{request_id}] 📊 Maven输出分析结果:")
    logger.info(f"[{request_id}]   测试运行: {analysis['tests_run']}")
    logger.info(f"[{request_id}]   测试失败: {analysis['tests_failed']}")
    logger.info(f"[{request_id}]   测试错误: {analysis['tests_errors']}")
    logger.info(f"[{request_id}]   测试跳过: {analysis['tests_skipped']}")
    logger.info(f"[{request_id}]   编译错误: {len(analysis['compilation_errors'])}")
    logger.info(f"[{request_id}]   构建警告: {len(analysis['build_warnings'])}")
    
    return analysis

def run_jacoco_scan_docker_debug(repo_url: str, commit_id: str, branch_name: str, 
                                reports_dir: str, service_config: Dict[str, Any], 
                                request_id: str) -> Dict[str, Any]:
    """运行JaCoCo Docker扫描（调试版本）"""
    logger.info(f"[{request_id}] 🚀 开始JaCoCo Docker扫描（调试模式）")
    logger.debug(f"[{request_id}] [DEBUG] 仓库URL: {repo_url}")
    logger.debug(f"[{request_id}] [DEBUG] 提交ID: {commit_id}")
    logger.debug(f"[{request_id}] [DEBUG] 分支名: {branch_name}")
    logger.debug(f"[{request_id}] [DEBUG] 报告目录: {reports_dir}")
    logger.debug(f"[{request_id}] [DEBUG] 服务配置: {service_config}")
    
    # 检查Docker环境
    if not _check_docker_available(request_id):
        logger.warning(f"[{request_id}] ⚠️  Docker不可用，回退到本地扫描")
        return run_jacoco_scan_local_debug(repo_url, commit_id, branch_name, reports_dir, service_config, request_id)
    
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix=f"jacoco_docker_{request_id}_")
        logger.debug(f"[{request_id}] [DEBUG] 临时目录: {temp_dir}")
        
        # 构建Docker命令
        docker_cmd = [
            'docker', 'run', '--rm',
            '-v', f"{temp_dir}:/workspace/reports",
            'jacoco-scanner:latest',
            repo_url, commit_id, branch_name
        ]
        
        logger.info(f"[{request_id}] 🐳 执行Docker扫描...")
        result = _run_maven_command(docker_cmd, temp_dir, request_id, "Docker扫描", 
                                   timeout=service_config.get('scan_timeout', 1800))
        
        # 分析输出
        analysis = _analyze_maven_output(result.stdout + result.stderr, request_id)
        
        # 复制报告文件
        if os.path.exists(temp_dir):
            logger.debug(f"[{request_id}] [DEBUG] 复制报告文件...")
            shutil.copytree(temp_dir, reports_dir, dirs_exist_ok=True)
        
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return {
            "status": "completed" if result.returncode == 0 else "failed",
            "method": "docker",
            "analysis": analysis,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except Exception as e:
        logger.error(f"[{request_id}] ❌ Docker扫描失败: {e}")
        return {
            "status": "error",
            "method": "docker",
            "error": str(e)
        }

def run_jacoco_scan_local_debug(repo_url: str, commit_id: str, branch_name: str, 
                               reports_dir: str, service_config: Dict[str, Any], 
                               request_id: str) -> Dict[str, Any]:
    """运行JaCoCo本地扫描（调试版本）"""
    logger.info(f"[{request_id}] 🏠 开始JaCoCo本地扫描（调试模式）")
    
    temp_dir = None
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix=f"jacoco_local_{request_id}_")
        logger.debug(f"[{request_id}] [DEBUG] 临时目录: {temp_dir}")
        
        # 克隆仓库
        logger.info(f"[{request_id}] 📥 克隆仓库...")
        clone_cmd = ['git', 'clone', '--depth', '1', '--branch', branch_name, repo_url, temp_dir]
        result = _run_maven_command(clone_cmd, os.getcwd(), request_id, "仓库克隆", timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"仓库克隆失败: {result.stderr}")
        
        # 检查项目结构
        logger.debug(f"[{request_id}] [DEBUG] 检查项目结构...")
        pom_file = os.path.join(temp_dir, "pom.xml")
        if not os.path.exists(pom_file):
            raise Exception("不是Maven项目，未找到pom.xml")
        
        logger.debug(f"[{request_id}] [DEBUG] 找到pom.xml文件")
        
        # 检查源代码和测试代码
        src_main = os.path.join(temp_dir, "src", "main", "java")
        src_test = os.path.join(temp_dir, "src", "test", "java")
        
        has_main = os.path.exists(src_main)
        has_test = os.path.exists(src_test)
        
        logger.info(f"[{request_id}] 📁 项目结构检查:")
        logger.info(f"[{request_id}]   主代码目录: {'✅' if has_main else '❌'} {src_main}")
        logger.info(f"[{request_id}]   测试代码目录: {'✅' if has_test else '❌'} {src_test}")
        
        if has_main:
            main_files = sum(1 for _, _, files in os.walk(src_main) for f in files if f.endswith('.java'))
            logger.info(f"[{request_id}]   主代码文件数: {main_files}")
        
        if has_test:
            test_files = sum(1 for _, _, files in os.walk(src_test) for f in files if f.endswith('.java'))
            logger.info(f"[{request_id}]   测试代码文件数: {test_files}")
        else:
            logger.warning(f"[{request_id}] ⚠️  没有测试代码，覆盖率将为0%")
        
        # 运行Maven命令
        maven_goals = service_config.get('maven_goals', ['clean', 'test', 'jacoco:report'])
        logger.info(f"[{request_id}] 🔨 执行Maven目标: {maven_goals}")
        
        all_output = ""
        analysis_combined = {
            "tests_run": 0, "tests_failed": 0, "tests_errors": 0, "tests_skipped": 0,
            "compilation_errors": [], "test_failures": [], "jacoco_info": [], "build_warnings": []
        }
        
        for i, goal in enumerate(maven_goals):
            step_name = f"Maven {goal} ({i+1}/{len(maven_goals)})"
            maven_cmd = ['mvn', goal, '-B', '-e']
            
            result = _run_maven_command(maven_cmd, temp_dir, request_id, step_name, timeout=600)
            all_output += result.stdout + result.stderr
            
            # 分析每个步骤的输出
            step_analysis = _analyze_maven_output(result.stdout + result.stderr, request_id)
            
            # 合并分析结果
            analysis_combined["tests_run"] += step_analysis["tests_run"]
            analysis_combined["tests_failed"] += step_analysis["tests_failed"]
            analysis_combined["tests_errors"] += step_analysis["tests_errors"]
            analysis_combined["tests_skipped"] += step_analysis["tests_skipped"]
            analysis_combined["compilation_errors"].extend(step_analysis["compilation_errors"])
            analysis_combined["test_failures"].extend(step_analysis["test_failures"])
            analysis_combined["jacoco_info"].extend(step_analysis["jacoco_info"])
            analysis_combined["build_warnings"].extend(step_analysis["build_warnings"])
            
            if result.returncode != 0 and goal in ['compile', 'test-compile']:
                logger.error(f"[{request_id}] ❌ 关键步骤失败: {goal}")
                break
        
        # 复制报告文件
        jacoco_reports = os.path.join(temp_dir, "target", "site", "jacoco")
        if os.path.exists(jacoco_reports):
            logger.info(f"[{request_id}] 📋 复制JaCoCo报告...")
            shutil.copytree(jacoco_reports, os.path.join(reports_dir, "html"), dirs_exist_ok=True)
            
            # 复制XML报告
            xml_report = os.path.join(temp_dir, "target", "site", "jacoco", "jacoco.xml")
            if os.path.exists(xml_report):
                shutil.copy2(xml_report, reports_dir)
                logger.debug(f"[{request_id}] [DEBUG] XML报告已复制")
        else:
            logger.warning(f"[{request_id}] ⚠️  JaCoCo报告目录不存在: {jacoco_reports}")
        
        return {
            "status": "completed",
            "method": "local",
            "analysis": analysis_combined,
            "full_output": all_output
        }
        
    except Exception as e:
        logger.error(f"[{request_id}] ❌ 本地扫描失败: {e}")
        return {
            "status": "error",
            "method": "local",
            "error": str(e)
        }
    finally:
        if temp_dir and os.path.exists(temp_dir):
            logger.debug(f"[{request_id}] [DEBUG] 清理临时目录: {temp_dir}")
            shutil.rmtree(temp_dir, ignore_errors=True)

def parse_jacoco_reports_debug(reports_dir: str, request_id: str) -> Dict[str, Any]:
    """解析JaCoCo报告（调试版本）"""
    logger.debug(f"[{request_id}] [DEBUG] 解析JaCoCo报告...")
    logger.debug(f"[{request_id}] [DEBUG] 报告目录: {reports_dir}")
    
    # 导入原始解析函数
    from .jacoco_tasks import parse_jacoco_reports
    
    result = parse_jacoco_reports(reports_dir, request_id)
    
    logger.debug(f"[{request_id}] [DEBUG] 报告解析结果: {result}")
    
    return result
