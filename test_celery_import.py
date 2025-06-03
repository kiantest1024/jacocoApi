#!/usr/bin/env python3
"""
测试 Celery 导入问题的脚本
用于验证 Python 3.12+ 兼容性修复
"""

import sys
import traceback

def test_basic_imports():
    """测试基本导入"""
    print("=== 测试基本导入 ===")
    
    try:
        import os
        print("✓ os")
    except Exception as e:
        print(f"✗ os: {e}")
    
    try:
        import logging
        print("✓ logging")
    except Exception as e:
        print(f"✗ logging: {e}")
    
    try:
        import subprocess
        print("✓ subprocess")
    except Exception as e:
        print(f"✗ subprocess: {e}")
    
    try:
        import json
        print("✓ json")
    except Exception as e:
        print(f"✗ json: {e}")
    
    try:
        import xml.etree.ElementTree as ET
        print("✓ xml.etree.ElementTree")
    except Exception as e:
        print(f"✗ xml.etree.ElementTree: {e}")

def test_third_party_imports():
    """测试第三方库导入"""
    print("\n=== 测试第三方库导入 ===")
    
    try:
        import fastapi
        print(f"✓ fastapi {fastapi.__version__}")
    except Exception as e:
        print(f"✗ fastapi: {e}")
    
    try:
        import uvicorn
        print(f"✓ uvicorn {uvicorn.__version__}")
    except Exception as e:
        print(f"✗ uvicorn: {e}")
    
    try:
        import celery
        print(f"✓ celery {celery.__version__}")
    except Exception as e:
        print(f"✗ celery: {e}")
    
    try:
        import redis
        print(f"✓ redis {redis.__version__}")
    except Exception as e:
        print(f"✗ redis: {e}")
    
    try:
        import requests
        print(f"✓ requests {requests.__version__}")
    except Exception as e:
        print(f"✗ requests: {e}")

def test_problematic_imports():
    """测试可能有问题的导入"""
    print("\n=== 测试可能有问题的导入 ===")
    
    # 测试 distutils（Python 3.12+ 中已移除）
    try:
        import distutils
        print(f"✓ distutils (意外可用)")
    except Exception as e:
        print(f"✗ distutils: {e} (这是预期的)")
    
    # 测试 setuptools（应该可以替代 distutils）
    try:
        import setuptools
        print(f"✓ setuptools {setuptools.__version__}")
    except Exception as e:
        print(f"✗ setuptools: {e}")
    
    # 测试 docker 库
    try:
        import docker
        print(f"✓ docker {docker.__version__}")
    except Exception as e:
        print(f"✗ docker: {e}")

def test_config_import():
    """测试配置文件导入"""
    print("\n=== 测试配置文件导入 ===")
    
    try:
        from config import settings, CELERY_BROKER_URL, CELERY_RESULT_BACKEND
        print("✓ config 模块导入成功")
        print(f"  CELERY_BROKER_URL: {CELERY_BROKER_URL}")
        print(f"  CELERY_RESULT_BACKEND: {CELERY_RESULT_BACKEND}")
    except Exception as e:
        print(f"✗ config: {e}")
        traceback.print_exc()

def test_celery_app():
    """测试 Celery 应用创建"""
    print("\n=== 测试 Celery 应用创建 ===")
    
    try:
        from celery import Celery
        
        # 创建简单的 Celery 应用
        app = Celery('test_app', broker='redis://localhost:6379/0')
        print("✓ Celery 应用创建成功")
        
        # 测试任务装饰器
        @app.task
        def test_task():
            return "Hello from Celery!"
        
        print("✓ Celery 任务装饰器工作正常")
        
    except Exception as e:
        print(f"✗ Celery 应用创建失败: {e}")
        traceback.print_exc()

def test_jacoco_tasks_import():
    """测试 jacoco_tasks 模块导入"""
    print("\n=== 测试 jacoco_tasks 模块导入 ===")
    
    try:
        import jacoco_tasks
        print("✓ jacoco_tasks 模块导入成功")
        
        # 检查 celery_app 是否存在
        if hasattr(jacoco_tasks, 'celery_app'):
            print("✓ celery_app 对象存在")
        else:
            print("✗ celery_app 对象不存在")
            
    except Exception as e:
        print(f"✗ jacoco_tasks 导入失败: {e}")
        traceback.print_exc()

def main():
    """主函数"""
    print("Python 版本:", sys.version)
    print("Python 路径:", sys.executable)
    print("=" * 50)
    
    test_basic_imports()
    test_third_party_imports()
    test_problematic_imports()
    test_config_import()
    test_celery_app()
    test_jacoco_tasks_import()
    
    print("\n" + "=" * 50)
    print("测试完成!")

if __name__ == "__main__":
    main()
