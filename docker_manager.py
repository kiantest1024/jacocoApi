#!/usr/bin/env python3
"""
Docker容器管理器
管理共享的JaCoCo扫描容器，支持并发处理
"""

import subprocess
import time
import json
import os
import threading
import logging
from typing import Dict, Any, Optional
import tempfile
import shutil

logger = logging.getLogger(__name__)

class DockerContainerManager:
    """Docker容器管理器"""
    
    def __init__(self):
        self.container_id = None
        self.container_name = "jacoco-scanner-shared"
        self.image_name = "jacoco-scanner:latest"
        self.is_running = False
        self.lock = threading.Lock()
        self.work_dir = "/tmp/jacoco_shared_work"
        
        # 确保工作目录存在
        os.makedirs(self.work_dir, exist_ok=True)
    
    def start_shared_container(self) -> bool:
        """启动共享容器"""
        with self.lock:
            if self.is_running:
                logger.info("共享容器已在运行")
                return True
            
            try:
                # 检查是否已有同名容器在运行
                existing = self._get_existing_container()
                if existing:
                    self.container_id = existing
                    self.is_running = True
                    logger.info(f"发现已运行的共享容器: {self.container_id}")
                    return True
                
                # 启动新的共享容器
                logger.info("启动新的共享JaCoCo扫描容器...")
                
                docker_cmd = [
                    "docker", "run", "-d",
                    "--name", self.container_name,
                    "-v", f"{self.work_dir}:/app/shared_work",
                    "-v", "/tmp:/tmp",  # 共享临时目录
                    "--workdir", "/app",
                    self.image_name,
                    "tail", "-f", "/dev/null"  # 保持容器运行
                ]
                
                result = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    self.container_id = result.stdout.strip()
                    self.is_running = True
                    logger.info(f"共享容器启动成功: {self.container_id}")
                    
                    # 等待容器完全启动
                    time.sleep(2)
                    return True
                else:
                    logger.error(f"启动共享容器失败: {result.stderr}")
                    return False
                    
            except Exception as e:
                logger.error(f"启动共享容器异常: {e}")
                return False
    
    def _get_existing_container(self) -> Optional[str]:
        """获取已存在的容器ID"""
        try:
            result = subprocess.run(
                ["docker", "ps", "-q", "--filter", f"name={self.container_name}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
            
        except Exception as e:
            logger.warning(f"检查已存在容器失败: {e}")
            return None
    
    def execute_scan(self, repo_url: str, commit_id: str, branch_name: str, 
                    service_name: str, request_id: str) -> Dict[str, Any]:
        """在共享容器中执行扫描"""
        if not self.is_running:
            if not self.start_shared_container():
                raise Exception("无法启动共享容器")
        
        try:
            # 创建任务目录
            task_dir = os.path.join(self.work_dir, f"task_{request_id}")
            os.makedirs(task_dir, exist_ok=True)
            
            # 创建任务配置文件
            task_config = {
                "repo_url": repo_url,
                "commit_id": commit_id,
                "branch_name": branch_name,
                "service_name": service_name,
                "request_id": request_id,
                "task_dir": f"/app/shared_work/task_{request_id}"
            }
            
            config_file = os.path.join(task_dir, "task_config.json")
            with open(config_file, 'w') as f:
                json.dump(task_config, f, indent=2)
            
            logger.info(f"[{request_id}] 在共享容器中执行扫描...")
            
            # 在容器中执行扫描脚本
            docker_exec_cmd = [
                "docker", "exec", self.container_id,
                "/app/scripts/shared_scan.sh",
                f"/app/shared_work/task_{request_id}/task_config.json"
            ]
            
            result = subprocess.run(
                docker_exec_cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            # 读取结果
            result_file = os.path.join(task_dir, "scan_result.json")
            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    scan_result = json.load(f)
            else:
                scan_result = {
                    "status": "failed",
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "error": "未找到结果文件"
                }
            
            # 清理任务目录
            try:
                shutil.rmtree(task_dir)
            except Exception as e:
                logger.warning(f"清理任务目录失败: {e}")
            
            return scan_result
            
        except subprocess.TimeoutExpired:
            logger.error(f"[{request_id}] 共享容器扫描超时")
            return {
                "status": "timeout",
                "error": "扫描超时"
            }
        except Exception as e:
            logger.error(f"[{request_id}] 共享容器扫描异常: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def stop_shared_container(self):
        """停止共享容器"""
        with self.lock:
            if not self.is_running:
                return
            
            try:
                logger.info("停止共享容器...")
                subprocess.run(
                    ["docker", "stop", self.container_name],
                    capture_output=True,
                    timeout=30
                )
                
                subprocess.run(
                    ["docker", "rm", self.container_name],
                    capture_output=True,
                    timeout=30
                )
                
                self.container_id = None
                self.is_running = False
                logger.info("共享容器已停止")
                
            except Exception as e:
                logger.error(f"停止共享容器失败: {e}")
    
    def get_container_status(self) -> Dict[str, Any]:
        """获取容器状态"""
        if not self.container_id:
            return {"status": "not_started"}
        
        try:
            result = subprocess.run(
                ["docker", "inspect", self.container_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                inspect_data = json.loads(result.stdout)[0]
                state = inspect_data.get("State", {})
                
                return {
                    "status": "running" if state.get("Running") else "stopped",
                    "container_id": self.container_id,
                    "started_at": state.get("StartedAt"),
                    "uptime": self._calculate_uptime(state.get("StartedAt"))
                }
            else:
                return {"status": "not_found"}
                
        except Exception as e:
            logger.error(f"获取容器状态失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_uptime(self, started_at: str) -> str:
        """计算容器运行时间"""
        if not started_at:
            return "unknown"
        
        try:
            from datetime import datetime
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            now = datetime.now(start_time.tzinfo)
            uptime = now - start_time
            
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}天{hours}小时{minutes}分钟"
            elif hours > 0:
                return f"{hours}小时{minutes}分钟"
            else:
                return f"{minutes}分钟"
                
        except Exception:
            return "unknown"

# 全局共享容器管理器实例
shared_container_manager = DockerContainerManager()

def get_shared_container_manager() -> DockerContainerManager:
    """获取共享容器管理器实例"""
    return shared_container_manager
