#!/usr/bin/env python3
"""
MySQL配置管理器
支持将配置数据存储到MySQL数据库中
"""

import json
import logging
import hashlib
from typing import Dict, List, Any
from datetime import datetime
from .database import get_db_manager, DatabaseManager

logger = logging.getLogger(__name__)

class MySQLConfigManager:
    """MySQL配置管理器"""
    
    def __init__(self):
        self.db_manager: DatabaseManager = get_db_manager()
    
    def get_lark_bots(self) -> Dict[str, Dict[str, Any]]:
        """获取所有机器人配置"""
        try:
            bots_data = self.db_manager.execute_query("""
                SELECT id, name, webhook_url, timeout, retry_count, is_custom
                FROM lark_bots
                ORDER BY created_at
            """)
            
            bots = {}
            for bot in bots_data:
                bots[bot['id']] = {
                    'name': bot['name'],
                    'webhook_url': bot['webhook_url'],
                    'timeout': bot['timeout'],
                    'retry_count': bot['retry_count'],
                    'is_custom': bool(bot['is_custom'])
                }
            
            return bots
            
        except Exception as e:
            logger.error(f"获取机器人配置失败: {e}")
            return {}
    
    def get_project_mappings(self) -> Dict[str, str]:
        """获取项目映射配置"""
        try:
            mappings_data = self.db_manager.execute_query("""
                SELECT project_name, bot_id
                FROM project_mappings
                ORDER BY created_at
            """)
            
            mappings = {}
            for mapping in mappings_data:
                mappings[mapping['project_name']] = mapping['bot_id']
            
            return mappings
            
        except Exception as e:
            logger.error(f"获取项目映射失败: {e}")
            return {}
    
    def add_bot(self, bot_id: str, bot_config: Dict[str, Any]) -> bool:
        """添加机器人配置"""
        try:
            # 记录操作历史
            self._record_history('CREATE', 'lark_bots', bot_id, None, bot_config)
            
            # 插入机器人配置
            insert_sql = """
            INSERT INTO lark_bots (id, name, webhook_url, timeout, retry_count, is_custom)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                webhook_url = VALUES(webhook_url),
                timeout = VALUES(timeout),
                retry_count = VALUES(retry_count),
                is_custom = VALUES(is_custom),
                updated_at = CURRENT_TIMESTAMP
            """
            
            params = (
                bot_id,
                bot_config.get('name', ''),
                bot_config.get('webhook_url', ''),
                bot_config.get('timeout', 10),
                bot_config.get('retry_count', 3),
                bot_config.get('is_custom', False)
            )
            
            rows_affected = self.db_manager.execute_update(insert_sql, params)
            
            if rows_affected > 0:
                logger.info(f"机器人配置已保存: {bot_id}")
                return True
            else:
                logger.warning(f"机器人配置保存失败: {bot_id}")
                return False
                
        except Exception as e:
            logger.error(f"添加机器人配置失败: {e}")
            return False
    
    def remove_bot(self, bot_id: str) -> bool:
        """删除机器人配置（仅限自定义机器人）"""
        try:
            # 检查是否为自定义机器人
            bot_data = self.db_manager.execute_query("""
                SELECT id, name, is_custom FROM lark_bots WHERE id = %s
            """, (bot_id,))
            
            if not bot_data:
                logger.warning(f"机器人不存在: {bot_id}")
                return False
            
            bot = bot_data[0]
            if not bot['is_custom']:
                logger.warning(f"不能删除预配置机器人: {bot_id}")
                return False
            
            # 记录操作历史
            self._record_history('DELETE', 'lark_bots', bot_id, bot, None)
            
            # 删除机器人（级联删除相关的项目映射）
            delete_sql = "DELETE FROM lark_bots WHERE id = %s AND is_custom = TRUE"
            rows_affected = self.db_manager.execute_update(delete_sql, (bot_id,))
            
            if rows_affected > 0:
                logger.info(f"自定义机器人已删除: {bot_id}")
                return True
            else:
                logger.warning(f"自定义机器人删除失败: {bot_id}")
                return False
                
        except Exception as e:
            logger.error(f"删除机器人配置失败: {e}")
            return False
    
    def add_project_mapping(self, project_name: str, bot_id: str, git_url: str = None) -> bool:
        """添加项目映射"""
        try:
            # 检查机器人是否存在
            bot_exists = self.db_manager.execute_query("""
                SELECT id FROM lark_bots WHERE id = %s
            """, (bot_id,))
            
            if not bot_exists:
                logger.error(f"机器人不存在: {bot_id}")
                return False
            
            # 记录操作历史
            mapping_data = {
                'project_name': project_name,
                'bot_id': bot_id,
                'git_url': git_url
            }
            self._record_history('CREATE', 'project_mappings', project_name, None, mapping_data)
            
            # 插入或更新项目映射
            insert_sql = """
            INSERT INTO project_mappings (project_name, git_url, bot_id)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                git_url = VALUES(git_url),
                bot_id = VALUES(bot_id),
                updated_at = CURRENT_TIMESTAMP
            """
            
            params = (project_name, git_url, bot_id)
            rows_affected = self.db_manager.execute_update(insert_sql, params)
            
            if rows_affected > 0:
                logger.info(f"项目映射已保存: {project_name} -> {bot_id}")
                return True
            else:
                logger.warning(f"项目映射保存失败: {project_name}")
                return False
                
        except Exception as e:
            logger.error(f"添加项目映射失败: {e}")
            return False
    
    def delete_project_mapping(self, project_name: str) -> bool:
        """删除项目映射"""
        try:
            # 获取现有映射数据用于历史记录
            existing_data = self.db_manager.execute_query("""
                SELECT project_name, git_url, bot_id FROM project_mappings WHERE project_name = %s
            """, (project_name,))
            
            if not existing_data:
                logger.warning(f"项目映射不存在: {project_name}")
                return False
            
            # 记录操作历史
            self._record_history('DELETE', 'project_mappings', project_name, existing_data[0], None)
            
            # 删除项目映射
            delete_sql = "DELETE FROM project_mappings WHERE project_name = %s"
            rows_affected = self.db_manager.execute_update(delete_sql, (project_name,))
            
            if rows_affected > 0:
                logger.info(f"项目映射已删除: {project_name}")
                return True
            else:
                logger.warning(f"项目映射删除失败: {project_name}")
                return False
                
        except Exception as e:
            logger.error(f"删除项目映射失败: {e}")
            return False
    
    def check_project_exists(self, project_name: str) -> Dict[str, Any]:
        """检查项目是否已配置"""
        try:
            project_data = self.db_manager.execute_query("""
                SELECT pm.project_name, pm.git_url, pm.bot_id, lb.name as bot_name, lb.webhook_url
                FROM project_mappings pm
                JOIN lark_bots lb ON pm.bot_id = lb.id
                WHERE pm.project_name = %s
            """, (project_name,))
            
            if project_data:
                project = project_data[0]
                return {
                    "exists": True,
                    "project_name": project['project_name'],
                    "git_url": project['git_url'],
                    "bot_id": project['bot_id'],
                    "bot_name": project['bot_name'],
                    "webhook_url": project['webhook_url']
                }
            else:
                return {"exists": False}
                
        except Exception as e:
            logger.error(f"检查项目配置失败: {e}")
            return {"exists": False, "error": str(e)}
    
    def get_system_config(self, config_key: str) -> Any:
        """获取系统配置"""
        try:
            config_data = self.db_manager.execute_query("""
                SELECT config_value FROM system_config WHERE config_key = %s
            """, (config_key,))
            
            if config_data:
                return json.loads(config_data[0]['config_value'])
            else:
                return None
                
        except Exception as e:
            logger.error(f"获取系统配置失败: {e}")
            return None
    
    def set_system_config(self, config_key: str, config_value: Any, description: str = None) -> bool:
        """设置系统配置"""
        try:
            insert_sql = """
            INSERT INTO system_config (config_key, config_value, description)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                config_value = VALUES(config_value),
                description = VALUES(description),
                updated_at = CURRENT_TIMESTAMP
            """
            
            params = (config_key, json.dumps(config_value), description)
            rows_affected = self.db_manager.execute_update(insert_sql, params)
            
            if rows_affected > 0:
                logger.info(f"系统配置已保存: {config_key}")
                return True
            else:
                logger.warning(f"系统配置保存失败: {config_key}")
                return False
                
        except Exception as e:
            logger.error(f"设置系统配置失败: {e}")
            return False
    
    def verify_admin_password(self, password: str) -> bool:
        """验证管理员密码"""
        try:
            stored_hash = self.get_system_config('admin_password_hash')
            if stored_hash:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                return password_hash == stored_hash
            else:
                # 如果没有设置密码，使用默认密码
                default_hash = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                return password_hash == default_hash
                
        except Exception as e:
            logger.error(f"验证管理员密码失败: {e}")
            return False
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态"""
        try:
            # 统计数据
            bots_count = self.db_manager.execute_query("SELECT COUNT(*) as count FROM lark_bots")[0]['count']
            mappings_count = self.db_manager.execute_query("SELECT COUNT(*) as count FROM project_mappings")[0]['count']
            custom_bots_count = self.db_manager.execute_query("SELECT COUNT(*) as count FROM lark_bots WHERE is_custom = TRUE")[0]['count']
            
            # 数据库信息
            db_info = self.db_manager.get_database_info()
            
            return {
                "storage_type": "MySQL",
                "total_bots": bots_count,
                "total_mappings": mappings_count,
                "custom_bots": custom_bots_count,
                "database_info": db_info,
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"获取配置状态失败: {e}")
            return {"error": str(e)}
    
    def _record_history(self, operation_type: str, table_name: str, record_id: str, 
                       old_data: Dict = None, new_data: Dict = None, operator: str = "system"):
        """记录操作历史"""
        try:
            insert_sql = """
            INSERT INTO config_history (operation_type, table_name, record_id, old_data, new_data, operator)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            params = (
                operation_type,
                table_name,
                record_id,
                json.dumps(old_data) if old_data else None,
                json.dumps(new_data) if new_data else None,
                operator
            )
            
            self.db_manager.execute_update(insert_sql, params)
            
        except Exception as e:
            logger.error(f"记录操作历史失败: {e}")
    
    def get_operation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取操作历史"""
        try:
            history_data = self.db_manager.execute_query("""
                SELECT operation_type, table_name, record_id, old_data, new_data, operator, created_at
                FROM config_history
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            
            history = []
            for record in history_data:
                history.append({
                    'operation_type': record['operation_type'],
                    'table_name': record['table_name'],
                    'record_id': record['record_id'],
                    'old_data': json.loads(record['old_data']) if record['old_data'] else None,
                    'new_data': json.loads(record['new_data']) if record['new_data'] else None,
                    'operator': record['operator'],
                    'created_at': record['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return history
            
        except Exception as e:
            logger.error(f"获取操作历史失败: {e}")
            return []

# 全局MySQL配置管理器实例
mysql_config_manager = None

def get_mysql_config_manager() -> MySQLConfigManager:
    """获取MySQL配置管理器实例"""
    global mysql_config_manager
    if mysql_config_manager is None:
        mysql_config_manager = MySQLConfigManager()
    return mysql_config_manager
