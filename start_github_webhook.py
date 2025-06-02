"""
GitHub Webhook JaCoCo API 启动脚本。
用于启动接收 GitHub webhook 并触发 JaCoCo 覆盖率统计的 API 服务。
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_dependencies():
    """检查必要的依赖是否已安装。"""
    logger.info("检查依赖...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'celery', 'redis', 'requests', 
        'pydantic', 'python-dotenv', 'pydantic-settings'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"缺少以下依赖包: {', '.join(missing_packages)}")
        logger.info("请运行: pip install -r requirements.txt")
        return False
    
    logger.info("✓ 所有依赖已安装")
    return True


def check_redis():
    """检查 Redis 是否可用。"""
    logger.info("检查 Redis 连接...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        logger.info("✓ Redis 连接正常")
        return True
    except Exception as e:
        logger.error(f"✗ Redis 连接失败: {str(e)}")
        logger.info("请确保 Redis 服务正在运行")
        return False


def check_java_maven():
    """检查 Java 和 Maven 是否可用。"""
    logger.info("检查 Java 和 Maven...")
    
    try:
        # 检查 Java
        java_result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        if java_result.returncode != 0:
            logger.error("✗ Java 未安装或不在 PATH 中")
            return False
        
        # 检查 Maven
        maven_result = subprocess.run(['mvn', '-version'], capture_output=True, text=True)
        if maven_result.returncode != 0:
            logger.error("✗ Maven 未安装或不在 PATH 中")
            return False
        
        logger.info("✓ Java 和 Maven 可用")
        return True
    except FileNotFoundError:
        logger.error("✗ Java 或 Maven 未找到")
        return False


def start_celery_worker():
    """启动 Celery worker。"""
    logger.info("启动 Celery worker...")
    
    try:
        # 启动 Celery worker 进程
        celery_cmd = [
            sys.executable, '-m', 'celery', 'worker',
            '-A', 'jacoco_tasks.celery_app',
            '--loglevel=info',
            '--concurrency=2'
        ]
        
        celery_process = subprocess.Popen(
            celery_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待一下确保启动
        time.sleep(3)
        
        if celery_process.poll() is None:
            logger.info("✓ Celery worker 已启动")
            return celery_process
        else:
            logger.error("✗ Celery worker 启动失败")
            return None
    except Exception as e:
        logger.error(f"✗ 启动 Celery worker 失败: {str(e)}")
        return None


def start_api_server():
    """启动 FastAPI 服务器。"""
    logger.info("启动 FastAPI 服务器...")
    
    try:
        # 启动 FastAPI 服务器
        api_cmd = [
            sys.executable, '-m', 'uvicorn',
            'main:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload'
        ]
        
        api_process = subprocess.Popen(
            api_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待一下确保启动
        time.sleep(5)
        
        if api_process.poll() is None:
            logger.info("✓ FastAPI 服务器已启动在 http://localhost:8000")
            return api_process
        else:
            logger.error("✗ FastAPI 服务器启动失败")
            return None
    except Exception as e:
        logger.error(f"✗ 启动 FastAPI 服务器失败: {str(e)}")
        return None


def main():
    """主函数。"""
    logger.info("=== GitHub Webhook JaCoCo API 启动器 ===")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    if not check_redis():
        logger.warning("Redis 不可用，某些功能可能无法正常工作")
    
    if not check_java_maven():
        logger.warning("Java 或 Maven 不可用，JaCoCo 扫描将无法工作")
    
    # 启动服务
    celery_process = None
    api_process = None
    
    try:
        # 启动 Celery worker
        celery_process = start_celery_worker()
        
        # 启动 API 服务器
        api_process = start_api_server()
        
        if api_process:
            logger.info("=== 服务启动完成 ===")
            logger.info("API 文档: http://localhost:8000/docs")
            logger.info("健康检查: http://localhost:8000/health")
            logger.info("GitHub Webhook: http://localhost:8000/github/webhook")
            logger.info("按 Ctrl+C 停止服务")
            
            # 等待进程
            try:
                api_process.wait()
            except KeyboardInterrupt:
                logger.info("收到停止信号...")
        
    except KeyboardInterrupt:
        logger.info("收到停止信号...")
    
    finally:
        # 清理进程
        if celery_process:
            logger.info("停止 Celery worker...")
            celery_process.terminate()
            celery_process.wait()
        
        if api_process:
            logger.info("停止 FastAPI 服务器...")
            api_process.terminate()
            api_process.wait()
        
        logger.info("服务已停止")


if __name__ == "__main__":
    main()
