"""
日志配置模块。
"""

import os
import logging.config
from typing import Dict, Any

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 日志配置
LOGGING_CONFIG: Dict[str, Any] = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'json': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'datefmt': '%Y-%m-%dT%H:%M:%S%z'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'filename': os.path.join(LOG_DIR, 'jacoco_api.log'),
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 10
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'standard',
            'filename': os.path.join(LOG_DIR, 'jacoco_api_error.log'),
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 10
        }
    },
    'loggers': {
        '': {  # 根记录器
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': True
        },
        'uvicorn': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'uvicorn.error': {
            'handlers': ['console', 'error_file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

def setup_logging():
    """设置日志配置。"""
    logging.config.dictConfig(LOGGING_CONFIG)
