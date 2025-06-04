#!/usr/bin/env python3
"""
配置管理工具
用于管理和验证JaCoCo API的配置
"""

import os
import json
from typing import Dict, Any, Optional
from config import LARK_CONFIG, DEFAULT_SCAN_CONFIG

def get_current_config() -> Dict[str, Any]:
    """获取当前配置"""
    return {
        "lark": LARK_CONFIG,
        "scan": DEFAULT_SCAN_CONFIG,
        "environment": {
            "DEBUG": os.getenv("DEBUG", "false"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "REDIS_HOST": os.getenv("REDIS_HOST", "localhost"),
            "REDIS_PORT": os.getenv("REDIS_PORT", "6379"),
            "REDIS_DB": os.getenv("REDIS_DB", "0"),
        }
    }

def validate_lark_config() -> Dict[str, Any]:
    """验证Lark配置"""
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # 检查webhook URL
    webhook_url = LARK_CONFIG.get("webhook_url", "")
    if not webhook_url:
        result["valid"] = False
        result["errors"].append("LARK_WEBHOOK_URL 未配置")
    elif not webhook_url.startswith("https://open.larksuite.com/"):
        result["warnings"].append("LARK_WEBHOOK_URL 格式可能不正确")
    
    # 检查超时设置
    timeout = LARK_CONFIG.get("timeout", 10)
    if timeout < 1 or timeout > 60:
        result["warnings"].append(f"LARK_TIMEOUT ({timeout}) 建议设置在1-60秒之间")
    
    # 检查重试设置
    retry_count = LARK_CONFIG.get("retry_count", 3)
    if retry_count < 0 or retry_count > 10:
        result["warnings"].append(f"LARK_RETRY_COUNT ({retry_count}) 建议设置在0-10之间")
    
    return result

def test_lark_connection() -> Dict[str, Any]:
    """测试Lark连接"""
    result = {
        "success": False,
        "message": "",
        "response_time": 0
    }
    
    try:
        import requests
        import time
        
        webhook_url = LARK_CONFIG.get("webhook_url")
        if not webhook_url:
            result["message"] = "未配置LARK_WEBHOOK_URL"
            return result
        
        # 发送测试消息
        test_message = {
            "msg_type": "text",
            "content": {
                "text": "🧪 JaCoCo API 配置测试消息"
            }
        }
        
        start_time = time.time()
        response = requests.post(
            webhook_url,
            json=test_message,
            timeout=LARK_CONFIG.get("timeout", 10)
        )
        end_time = time.time()
        
        result["response_time"] = round((end_time - start_time) * 1000, 2)  # 毫秒
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("code") == 0:
                result["success"] = True
                result["message"] = "Lark连接测试成功"
            else:
                result["message"] = f"Lark响应错误: {response_data.get('msg', '未知错误')}"
        else:
            result["message"] = f"HTTP错误: {response.status_code}"
            
    except Exception as e:
        result["message"] = f"连接异常: {str(e)}"
    
    return result

def print_config_summary():
    """打印配置摘要"""
    print("🔧 JaCoCo API 配置摘要")
    print("=" * 60)
    
    # Lark配置
    print("\n📱 Lark 通知配置:")
    print(f"  Webhook URL: {LARK_CONFIG['webhook_url'][:50]}...")
    print(f"  启用通知: {LARK_CONFIG['enable_notifications']}")
    print(f"  超时时间: {LARK_CONFIG['timeout']}秒")
    print(f"  重试次数: {LARK_CONFIG['retry_count']}")
    print(f"  重试延迟: {LARK_CONFIG['retry_delay']}秒")
    
    # 验证配置
    validation = validate_lark_config()
    if validation["valid"]:
        print("  ✅ 配置验证通过")
    else:
        print("  ❌ 配置验证失败:")
        for error in validation["errors"]:
            print(f"    - {error}")
    
    if validation["warnings"]:
        print("  ⚠️ 配置警告:")
        for warning in validation["warnings"]:
            print(f"    - {warning}")
    
    # 扫描配置
    print(f"\n🔍 扫描配置:")
    print(f"  Docker镜像: {DEFAULT_SCAN_CONFIG['docker_image']}")
    print(f"  使用Docker: {DEFAULT_SCAN_CONFIG['use_docker']}")
    print(f"  扫描超时: {DEFAULT_SCAN_CONFIG['scan_timeout']}秒")
    print(f"  覆盖率阈值: {DEFAULT_SCAN_CONFIG['coverage_threshold']}%")

def main():
    """主函数"""
    print_config_summary()
    
    print("\n" + "=" * 60)
    user_input = input("🤔 是否要测试Lark连接？(y/N): ").strip().lower()
    if user_input in ['y', 'yes']:
        print("\n🧪 测试Lark连接...")
        result = test_lark_connection()
        
        if result["success"]:
            print(f"✅ {result['message']} (响应时间: {result['response_time']}ms)")
        else:
            print(f"❌ {result['message']}")
    
    print("\n📋 配置文件位置:")
    print("  - 主配置: config.py")
    print("  - 环境配置: .env (基于 .env.example)")
    print("  - 修改配置后需要重启服务")

if __name__ == "__main__":
    main()
