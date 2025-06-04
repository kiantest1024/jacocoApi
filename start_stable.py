#!/usr/bin/env python3
"""
稳定的JaCoCo API服务启动脚本
解决异步任务和信号处理问题
"""

import os
import sys
import signal
import logging
import uvicorn
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_signal_handlers():
    """设置信号处理器"""
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在优雅关闭服务...")
        sys.exit(0)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Windows特殊处理
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, signal_handler)

def check_environment():
    """检查运行环境"""
    logger.info("🔍 检查运行环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    logger.info(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查必要文件
    required_files = ['app.py', 'config.py', 'jacoco_tasks.py']
    for file in required_files:
        if not os.path.exists(file):
            logger.error(f"❌ 缺少必要文件: {file}")
            return False
        else:
            logger.info(f"✅ 找到文件: {file}")
    
    # 检查Docker（可选）
    try:
        import subprocess
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info(f"✅ Docker可用: {result.stdout.strip()}")
        else:
            logger.warning("⚠️ Docker不可用，将使用本地扫描")
    except Exception as e:
        logger.warning(f"⚠️ Docker检查失败: {e}")
    
    return True

def start_server():
    """启动服务器"""
    # 检查环境
    if not check_environment():
        logger.error("❌ 环境检查失败，无法启动服务")
        return False
    
    # 设置信号处理
    setup_signal_handlers()
    
    # 服务配置
    port = 8002
    host = "0.0.0.0"
    
    logger.info("🚀 启动JaCoCo Scanner API服务...")
    logger.info(f"📡 服务地址: http://localhost:{port}")
    logger.info(f"📖 API文档: http://localhost:{port}/docs")
    logger.info(f"📊 报告列表: http://localhost:{port}/reports")
    
    try:
        # 使用更稳定的配置启动服务
        config = uvicorn.Config(
            "app:app",
            host=host,
            port=port,
            reload=False,  # 禁用热重载
            log_level="info",
            access_log=True,
            loop="asyncio",
            workers=1,  # 单进程避免复杂性
            timeout_keep_alive=30,
            timeout_graceful_shutdown=10
        )
        
        server = uvicorn.Server(config)
        
        logger.info("✅ 服务配置完成，开始监听请求...")
        server.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 服务被用户中断")
        return True
    except OSError as e:
        if "10048" in str(e) or "Address already in use" in str(e):
            logger.error(f"❌ 端口 {port} 被占用")
            logger.info("💡 解决方案:")
            logger.info(f"   1. 使用其他端口: python start_stable.py --port 8003")
            logger.info(f"   2. 或者终止占用端口的进程")
            return False
        else:
            logger.error(f"❌ 网络错误: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False
    finally:
        logger.info("🔚 服务已关闭")
        return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='JaCoCo Scanner API 稳定启动器')
    parser.add_argument('--port', type=int, default=8002, help='服务端口 (默认: 8002)')
    parser.add_argument('--host', default='0.0.0.0', help='服务主机 (默认: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🐛 调试模式已启用")
    
    # 更新全局端口配置
    global port
    port = args.port
    
    logger.info("🎯 JaCoCo Scanner API 稳定启动器")
    logger.info("=" * 50)
    
    success = start_server()
    
    if success:
        logger.info("✅ 服务正常关闭")
        sys.exit(0)
    else:
        logger.error("❌ 服务异常退出")
        sys.exit(1)

if __name__ == "__main__":
    main()
