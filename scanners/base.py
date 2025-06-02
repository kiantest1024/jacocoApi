"""
扫描器策略的基类。
"""

import abc
from typing import Dict, Any, Optional


class BaseScannerStrategy(abc.ABC):
    """
    扫描器策略的抽象基类。
    使用策略设计模式允许不同的扫描实现。
    """
    
    @abc.abstractmethod
    def scan(self, repo_url: str, commit_id: str, branch_name: str, 
             service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行代码覆盖率扫描。
        
        参数:
            repo_url: 仓库 URL
            commit_id: 要扫描的提交 ID
            branch_name: 分支名称
            service_config: 服务配置字典
            
        返回:
            包含扫描结果的字典
        """
        pass
    
    @abc.abstractmethod
    def parse_results(self, results_path: str) -> Dict[str, Any]:
        """
        解析扫描结果文件。
        
        参数:
            results_path: 结果文件的路径
            
        返回:
            包含解析结果的字典
        """
        pass
    
    def clone_repository(self, repo_url: str, target_dir: str, 
                         commit_id: Optional[str] = None) -> bool:
        """
        克隆仓库并检出特定提交。
        
        参数:
            repo_url: 仓库 URL
            target_dir: 目标目录
            commit_id: 要检出的提交 ID（如果为 None，则检出最新提交）
            
        返回:
            如果成功则为 True，否则为 False
        """
        import os
        import subprocess
        import tempfile
        import shutil
        
        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)
        
        try:
            # 克隆仓库
            subprocess.run(
                ["git", "clone", repo_url, target_dir],
                check=True,
                capture_output=True
            )
            
            # 如果指定了提交 ID，则检出该提交
            if commit_id:
                subprocess.run(
                    ["git", "checkout", commit_id],
                    check=True,
                    capture_output=True,
                    cwd=target_dir
                )
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"克隆仓库时出错: {e}")
            print(f"标准输出: {e.stdout.decode('utf-8')}")
            print(f"标准错误: {e.stderr.decode('utf-8')}")
            
            # 清理目标目录
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            
            return False
