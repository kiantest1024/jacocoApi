#!/usr/bin/env python3
"""
本地JaCoCo扫描功能（不使用Docker）
"""

import os
import subprocess
import tempfile
import shutil
import logging
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_local_jacoco_scan(repo_url: str, commit_id: str, branch_name: str, reports_dir: str, service_config: Dict, request_id: str) -> Dict[str, Any]:
    """
    本地JaCoCo扫描（不使用Docker）
    """
    logger.info(f"[{request_id}] 开始本地JaCoCo扫描")
    logger.info(f"[{request_id}] Repository: {repo_url}")
    logger.info(f"[{request_id}] Commit: {commit_id}")
    logger.info(f"[{request_id}] Branch: {branch_name}")
    
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
        
        # 4. 备份原始pom.xml
        pom_backup = os.path.join(repo_dir, "pom.xml.backup")
        shutil.copy2(pom_path, pom_backup)
        
        # 5. 增强pom.xml以支持JaCoCo
        enhance_pom_for_jacoco(pom_path, request_id)
        
        # 6. 运行Maven测试和JaCoCo
        logger.info(f"[{request_id}] 运行Maven测试和JaCoCo...")
        
        maven_cmd = [
            "mvn", "clean", "test", 
            "jacoco:report",
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
        
        # 7. 查找并复制JaCoCo报告
        jacoco_xml = os.path.join(repo_dir, "target", "site", "jacoco", "jacoco.xml")
        jacoco_html_dir = os.path.join(repo_dir, "target", "site", "jacoco")
        
        scan_result = {
            "status": "completed" if result.returncode == 0 else "partial",
            "maven_output": result.stdout,
            "maven_errors": result.stderr,
            "return_code": result.returncode,
            "reports_found": False
        }
        
        if os.path.exists(jacoco_xml):
            logger.info(f"[{request_id}] 找到JaCoCo XML报告")
            scan_result["reports_found"] = True
            
            # 复制报告到输出目录
            os.makedirs(reports_dir, exist_ok=True)
            shutil.copy2(jacoco_xml, reports_dir)
            
            if os.path.exists(jacoco_html_dir):
                html_output = os.path.join(reports_dir, "html")
                if os.path.exists(html_output):
                    shutil.rmtree(html_output)
                shutil.copytree(jacoco_html_dir, html_output)
                logger.info(f"[{request_id}] 复制HTML报告到: {html_output}")
        else:
            logger.warning(f"[{request_id}] 未找到JaCoCo报告")
            # 检查是否有其他位置的报告
            for root, dirs, files in os.walk(repo_dir):
                for file in files:
                    if file == "jacoco.xml":
                        found_path = os.path.join(root, file)
                        logger.info(f"[{request_id}] 在其他位置找到报告: {found_path}")
                        shutil.copy2(found_path, reports_dir)
                        scan_result["reports_found"] = True
                        break
        
        return scan_result
        
    except subprocess.TimeoutExpired:
        logger.error(f"[{request_id}] 扫描超时")
        return {"status": "timeout", "message": "扫描超时"}
    except Exception as e:
        logger.error(f"[{request_id}] 扫描失败: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"[{request_id}] 清理临时目录完成")
        except Exception as cleanup_error:
            logger.warning(f"[{request_id}] 清理失败: {cleanup_error}")

def enhance_pom_for_jacoco(pom_path: str, request_id: str):
    """增强pom.xml以支持JaCoCo"""
    try:
        # 读取pom.xml
        tree = ET.parse(pom_path)
        root = tree.getroot()
        
        # 获取命名空间
        namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
        if root.tag.startswith('{'):
            namespace_uri = root.tag[1:root.tag.index('}')]
            namespace = {'maven': namespace_uri}
        
        # 查找或创建properties
        properties = root.find('.//maven:properties', namespace)
        if properties is None:
            properties = ET.SubElement(root, 'properties')
        
        # 添加JaCoCo版本属性
        jacoco_version = ET.SubElement(properties, 'jacoco.version')
        jacoco_version.text = '0.8.7'
        
        # 查找或创建build
        build = root.find('.//maven:build', namespace)
        if build is None:
            build = ET.SubElement(root, 'build')
        
        # 查找或创建plugins
        plugins = build.find('.//maven:plugins', namespace)
        if plugins is None:
            plugins = ET.SubElement(build, 'plugins')
        
        # 添加JaCoCo插件
        jacoco_plugin = ET.SubElement(plugins, 'plugin')
        
        group_id = ET.SubElement(jacoco_plugin, 'groupId')
        group_id.text = 'org.jacoco'
        
        artifact_id = ET.SubElement(jacoco_plugin, 'artifactId')
        artifact_id.text = 'jacoco-maven-plugin'
        
        version = ET.SubElement(jacoco_plugin, 'version')
        version.text = '${jacoco.version}'
        
        executions = ET.SubElement(jacoco_plugin, 'executions')
        
        # prepare-agent execution
        execution1 = ET.SubElement(executions, 'execution')
        goals1 = ET.SubElement(execution1, 'goals')
        goal1 = ET.SubElement(goals1, 'goal')
        goal1.text = 'prepare-agent'
        
        # report execution
        execution2 = ET.SubElement(executions, 'execution')
        ex2_id = ET.SubElement(execution2, 'id')
        ex2_id.text = 'report'
        ex2_phase = ET.SubElement(execution2, 'phase')
        ex2_phase.text = 'test'
        goals2 = ET.SubElement(execution2, 'goals')
        goal2 = ET.SubElement(goals2, 'goal')
        goal2.text = 'report'
        
        # 写回文件
        tree.write(pom_path, encoding='utf-8', xml_declaration=True)
        logger.info(f"[{request_id}] pom.xml已增强支持JaCoCo")
        
    except Exception as e:
        logger.warning(f"[{request_id}] 增强pom.xml失败: {str(e)}")
        # 继续执行，可能原pom.xml已经有JaCoCo配置

if __name__ == "__main__":
    # 测试本地扫描
    test_repo = "http://172.16.1.30/kian/jacocotest.git"
    test_commit = "84d32a75d4832dc26f33678706bc8446da51cda0"
    test_branch = "main"
    test_reports = "/tmp/test_reports"
    test_config = {"service_name": "jacocotest"}
    test_id = "local_test_001"
    
    result = run_local_jacoco_scan(test_repo, test_commit, test_branch, test_reports, test_config, test_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))
