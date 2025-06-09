#!/usr/bin/env python3
"""
JaCoCo API 服务启动脚本
"""

import os
import sys
import logging

def setup_environment():
    """设置环境变量"""
    # 设置MySQL配置
    os.environ.setdefault('CONFIG_STORAGE_TYPE', 'mysql')
    os.environ.setdefault('MYSQL_HOST', '172.16.1.30')
    os.environ.setdefault('MYSQL_PORT', '3306')
    os.environ.setdefault('MYSQL_DATABASE', 'jacoco_config')
    os.environ.setdefault('MYSQL_USER', 'jacoco')
    os.environ.setdefault('MYSQL_PASSWORD', 'asd301325..')

def main():
    """主函数"""
    setup_environment()
    
    # 导入并启动应用
    try:
        from app import start_server
        start_server()
    except KeyboardInterrupt:
        print("\n服务被用户中断")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
