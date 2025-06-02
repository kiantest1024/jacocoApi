"""
Solution2 扫描器策略实现。
这是一个替代的扫描方法实现示例。
"""

import os
import subprocess
import tempfile
import shutil
import json
from typing import Dict, Any

from .base import BaseScannerStrategy


class Solution2ScannerStrategy(BaseScannerStrategy):
    """
    Solution2 扫描器策略实现。
    这是一个使用不同工具或方法的替代扫描实现。
    """
    
    def scan(self, repo_url: str, commit_id: str, branch_name: str, 
             service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用替代方法执行代码覆盖率扫描。
        
        参数:
            repo_url: 仓库 URL
            commit_id: 要扫描的提交 ID
            branch_name: 分支名称
            service_config: 服务配置字典
            
        返回:
            包含扫描结果的字典
        """
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="solution2_scan_")
        
        try:
            # 克隆仓库
            repo_dir = os.path.join(temp_dir, "repo")
            if not self.clone_repository(repo_url, repo_dir, commit_id):
                return {
                    "status": "error",
                    "message": f"无法克隆仓库 {repo_url} 或检出提交 {commit_id}"
                }
            
            # 获取配置
            coverage_settings_path = service_config.get('coverage_settings_path')
            custom_command = service_config.get('custom_command')
            
            # 创建结果目录
            results_dir = os.path.join(temp_dir, "results")
            os.makedirs(results_dir, exist_ok=True)
            
            # 执行自定义命令（如果提供）
            if custom_command:
                try:
                    # 替换命令中的占位符
                    command = custom_command.replace("{repo_dir}", repo_dir)
                    command = command.replace("{results_dir}", results_dir)
                    
                    subprocess.run(
                        command,
                        shell=True,
                        check=True,
                        capture_output=True,
                        cwd=repo_dir
                    )
                except subprocess.CalledProcessError as e:
                    return {
                        "status": "error",
                        "message": f"自定义命令执行失败: {e.stderr.decode('utf-8')}"
                    }
            
            # 否则，执行默认的覆盖率工具
            else:
                # 这里是一个示例，使用 coverage.py 工具（用于 Python 项目）
                try:
                    # 安装依赖
                    subprocess.run(
                        ["pip", "install", "-r", "requirements.txt"],
                        check=True,
                        capture_output=True,
                        cwd=repo_dir
                    )
                    
                    # 运行覆盖率工具
                    coverage_json = os.path.join(results_dir, "coverage.json")
                    
                    subprocess.run(
                        ["coverage", "run", "--source=.", "-m", "pytest"],
                        check=True,
                        capture_output=True,
                        cwd=repo_dir
                    )
                    
                    subprocess.run(
                        ["coverage", "json", "-o", coverage_json],
                        check=True,
                        capture_output=True,
                        cwd=repo_dir
                    )
                    
                except subprocess.CalledProcessError as e:
                    return {
                        "status": "error",
                        "message": f"覆盖率工具执行失败: {e.stderr.decode('utf-8')}"
                    }
            
            # 解析结果
            results_file = os.path.join(results_dir, "coverage.json")
            if os.path.exists(results_file):
                results = self.parse_results(results_file)
                results["status"] = "success"
                results["settings_used"] = coverage_settings_path
                return results
            else:
                return {
                    "status": "error",
                    "message": "覆盖率报告文件未生成"
                }
        
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)
    
    def parse_results(self, results_path: str) -> Dict[str, Any]:
        """
        解析 coverage.py JSON 报告文件。
        
        参数:
            results_path: coverage.py JSON 报告文件的路径
            
        返回:
            包含解析结果的字典
        """
        try:
            with open(results_path, 'r') as f:
                data = json.load(f)
            
            # 提取总体覆盖率数据
            totals = data.get("totals", {})
            
            # 获取行覆盖率
            line_covered = totals.get("covered_lines", 0)
            line_total = totals.get("num_statements", 0)
            
            # 计算覆盖率百分比
            coverage_percentage = (line_covered / line_total * 100) if line_total > 0 else 0
            
            # 构建结果字典
            result = {
                "coverage_percentage": round(coverage_percentage, 2),
                "lines_covered": line_covered,
                "lines_total": line_total,
                "detailed_coverage": {
                    "line_coverage": round(coverage_percentage, 2),
                    "branch_coverage": round(totals.get("covered_branches", 0) / totals.get("num_branches", 1) * 100, 2) if totals.get("num_branches", 0) > 0 else 0,
                    "missing_lines": totals.get("missing_lines", 0)
                }
            }
            
            return result
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"解析覆盖率报告时出错: {str(e)}",
                "coverage_percentage": 0,
                "lines_covered": 0,
                "lines_total": 0
            }
