#!/usr/bin/env python3
"""
简化的JaCoCo扫描功能
用于测试和调试
"""

import os
import subprocess
import tempfile
import shutil
import logging
import json
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simple_jacoco_scan(repo_url: str, commit_id: str, branch_name: str, request_id: str) -> Dict[str, Any]:
    """
    简化的JaCoCo扫描功能
    """
    logger.info(f"[{request_id}] 开始简化 JaCoCo 扫描")
    logger.info(f"[{request_id}] 仓库: {repo_url}")
    logger.info(f"[{request_id}] 提交: {commit_id}")
    logger.info(f"[{request_id}] 分支: {branch_name}")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix=f"jacoco_simple_{request_id}_")
    repo_dir = os.path.join(temp_dir, "repo")
    reports_dir = os.path.join(temp_dir, "reports")
    
    try:
        os.makedirs(repo_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)
        
        # 1. 克隆仓库
        logger.info(f"[{request_id}] 克隆仓库...")
        clone_cmd = ["git", "clone", repo_url, repo_dir]
        result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"克隆仓库失败: {result.stderr}")
        
        # 2. 切换到指定提交
        logger.info(f"[{request_id}] 切换到提交 {commit_id}")
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
        logger.info(f"[{request_id}] 运行Maven测试...")
        
        # 简单的Maven命令
        maven_cmd = [
            "mvn", "clean", "test", 
            "org.jacoco:jacoco-maven-plugin:prepare-agent",
            "org.jacoco:jacoco-maven-plugin:report",
            "-Dmaven.test.failure.ignore=true"
        ]
        
        result = subprocess.run(
            maven_cmd, 
            cwd=repo_dir, 
            capture_output=True, 
            text=True, 
            timeout=600
        )
        
        logger.info(f"[{request_id}] Maven执行完成，返回码: {result.returncode}")
        
        # 5. 查找JaCoCo报告
        jacoco_xml = os.path.join(repo_dir, "target", "site", "jacoco", "jacoco.xml")
        jacoco_html_dir = os.path.join(repo_dir, "target", "site", "jacoco")
        
        scan_result = {
            "status": "completed" if result.returncode == 0 else "partial",
            "maven_output": result.stdout,
            "maven_errors": result.stderr,
            "return_code": result.returncode,
            "reports_found": False,
            "coverage_data": None
        }
        
        if os.path.exists(jacoco_xml):
            logger.info(f"[{request_id}] 找到JaCoCo XML报告")
            scan_result["reports_found"] = True
            
            # 复制报告到输出目录
            shutil.copy2(jacoco_xml, reports_dir)
            if os.path.exists(jacoco_html_dir):
                shutil.copytree(jacoco_html_dir, os.path.join(reports_dir, "html"))
            
            # 简单解析覆盖率
            try:
                coverage_data = parse_simple_jacoco_xml(jacoco_xml, request_id)
                scan_result["coverage_data"] = coverage_data
            except Exception as parse_error:
                logger.warning(f"[{request_id}] 解析覆盖率失败: {parse_error}")
        else:
            logger.warning(f"[{request_id}] 未找到JaCoCo报告")
        
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

def parse_simple_jacoco_xml(xml_path: str, request_id: str) -> Dict[str, Any]:
    """简单解析JaCoCo XML报告"""
    try:
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 统计覆盖率
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
            "line_coverage": round(line_coverage, 2),
            "branch_coverage": round(branch_coverage, 2),
            "lines_covered": covered_lines,
            "lines_total": total_lines,
            "branches_covered": covered_branches,
            "branches_total": total_branches
        }
        
        logger.info(f"[{request_id}] 覆盖率解析完成 - 行覆盖率: {line_coverage:.2f}%")
        return result
        
    except Exception as e:
        logger.error(f"[{request_id}] XML解析失败: {str(e)}")
        raise

def test_scan():
    """测试扫描功能"""
    repo_url = "http://172.16.1.30/kian/jacocotest.git"
    commit_id = "84d32a75d4832dc26f33678706bc8446da51cda0"
    branch_name = "main"
    request_id = "test_001"
    
    print("开始测试扫描...")
    result = simple_jacoco_scan(repo_url, commit_id, branch_name, request_id)
    
    print("\n扫描结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_scan()
