#!/usr/bin/env python3
"""
Docker环境配置管理器
支持动态配置持久化和热重载
"""

import json
import importlib
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class DockerConfigManager:
    """Docker环境配置管理器"""
    
    def __init__(self):
        self.config_dir = Path("/app/config")
        self.config_file = self.config_dir / "dynamic_config.json"
        self.config_dir.mkdir(exist_ok=True)
        
        # 确保配置文件存在
        if not self.config_file.exists():
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            "lark_bots": {
                "default": {
                    "webhook_url": "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe",
                    "name": "默认机器人",
                    "timeout": 10,
                    "retry_count": 3,
                    "is_custom": False,
                }
            },
            "project_mappings": {
                "jacocotest": "default"
            },
            "version": "1.0.0",
            "last_updated": None
        }

        self._save_config(default_config)
        logger.info("创建默认配置文件")
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置到文件"""
        import time
        config["last_updated"] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def _load_config(self) -> Dict[str, Any]:
        """从文件加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._create_default_config()
            return self._load_config()
    
    def get_lark_bots(self) -> Dict[str, Dict[str, Any]]:
        """获取所有机器人配置"""
        config = self._load_config()
        return config.get("lark_bots", {})
    
    def get_project_mappings(self) -> Dict[str, str]:
        """获取项目映射配置"""
        config = self._load_config()
        return config.get("project_mappings", {})
    
    def add_bot(self, bot_id: str, bot_config: Dict[str, Any]) -> bool:
        """添加机器人配置"""
        try:
            config = self._load_config()
            config["lark_bots"][bot_id] = bot_config
            self._save_config(config)
            self._reload_config_module()
            logger.info(f"添加机器人配置: {bot_id}")
            return True
        except Exception as e:
            logger.error(f"添加机器人配置失败: {e}")
            return False

    def remove_bot(self, bot_id: str) -> bool:
        """删除机器人配置（仅限自定义机器人）"""
        try:
            config = self._load_config()
            if bot_id in config["lark_bots"]:
                bot_config = config["lark_bots"][bot_id]
                # 只允许删除自定义机器人
                if bot_config.get("is_custom", False):
                    del config["lark_bots"][bot_id]
                    self._save_config(config)
                    self._reload_config_module()
                    logger.info(f"删除机器人配置: {bot_id}")
                    return True
                else:
                    logger.warning(f"不能删除预配置机器人: {bot_id}")
                    return False
            return False
        except Exception as e:
            logger.error(f"删除机器人配置失败: {e}")
            return False

    def check_project_exists(self, project_name: str) -> Dict[str, Any]:
        """检查项目是否已配置"""
        try:
            config = self._load_config()
            mappings = config.get("project_mappings", {})

            if project_name in mappings:
                bot_id = mappings[project_name]
                bots = config.get("lark_bots", {})
                bot_config = bots.get(bot_id, {})

                return {
                    "exists": True,
                    "project_name": project_name,
                    "bot_id": bot_id,
                    "bot_name": bot_config.get("name", "未知机器人"),
                    "webhook_url": bot_config.get("webhook_url", "")
                }

            return {"exists": False}
        except Exception as e:
            logger.error(f"检查项目配置失败: {e}")
            return {"exists": False, "error": str(e)}
    
    def add_project_mapping(self, project_name: str, bot_id: str) -> bool:
        """添加项目映射"""
        try:
            config = self._load_config()
            config["project_mappings"][project_name] = bot_id
            self._save_config(config)
            self._reload_config_module()
            logger.info(f"添加项目映射: {project_name} -> {bot_id}")
            return True
        except Exception as e:
            logger.error(f"添加项目映射失败: {e}")
            return False
    
    def delete_project_mapping(self, project_name: str) -> bool:
        """删除项目映射"""
        try:
            config = self._load_config()
            if project_name in config["project_mappings"]:
                del config["project_mappings"][project_name]
                self._save_config(config)
                self._reload_config_module()
                logger.info(f"删除项目映射: {project_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除项目映射失败: {e}")
            return False
    
    def _reload_config_module(self):
        """重新加载配置模块"""
        try:
            # 动态更新config模块
            from config import config
            
            # 更新机器人配置
            config.LARK_BOTS.clear()
            config.LARK_BOTS.update(self.get_lark_bots())
            
            # 更新项目映射
            config.PROJECT_BOT_MAPPING.clear()
            config.PROJECT_BOT_MAPPING.update(self.get_project_mappings())
            
            # 重新加载模块
            importlib.reload(config)
            
            logger.info("配置模块重新加载成功")
        except Exception as e:
            logger.error(f"重新加载配置模块失败: {e}")
    
    def export_config(self) -> Dict[str, Any]:
        """导出完整配置"""
        return self._load_config()
    
    def import_config(self, config: Dict[str, Any]) -> bool:
        """导入配置"""
        try:
            # 验证配置格式
            required_keys = ["lark_bots", "project_mappings"]
            for key in required_keys:
                if key not in config:
                    raise ValueError(f"配置缺少必需字段: {key}")
            
            self._save_config(config)
            self._reload_config_module()
            logger.info("配置导入成功")
            return True
        except Exception as e:
            logger.error(f"配置导入失败: {e}")
            return False
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态"""
        config = self._load_config()
        return {
            "config_file": str(self.config_file),
            "config_exists": self.config_file.exists(),
            "total_bots": len(config.get("lark_bots", {})),
            "total_mappings": len(config.get("project_mappings", {})),
            "version": config.get("version", "unknown"),
            "last_updated": config.get("last_updated", "unknown")
        }

# 全局配置管理器实例
docker_config_manager = DockerConfigManager()

def init_docker_config():
    """初始化Docker配置"""
    try:
        # 加载持久化配置到config模块
        docker_config_manager._reload_config_module()
        logger.info("Docker配置初始化成功")
        return True
    except Exception as e:
        logger.error(f"Docker配置初始化失败: {e}")
        return False

def get_docker_config_manager():
    """获取配置管理器实例"""
    return docker_config_manager
