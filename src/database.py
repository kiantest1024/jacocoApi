#!/usr/bin/env python3
"""
MySQL数据库连接和操作模块
"""

import os
import json
import logging
import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import time

logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'database': os.getenv('MYSQL_DATABASE', 'jacoco_config'),
    'user': os.getenv('MYSQL_USER', 'jacoco_user'),
    'password': os.getenv('MYSQL_PASSWORD', 'jacoco_password'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True,
    'pool_name': 'jacoco_pool',
    'pool_size': 5,
    'pool_reset_session': True
}

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.config = DATABASE_CONFIG.copy()
        self.connection_pool = None
        self._init_connection_pool()
    
    def _init_connection_pool(self):
        """初始化连接池"""
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(**self.config)
            logger.info("MySQL连接池初始化成功")
        except Error as e:
            logger.error(f"MySQL连接池初始化失败: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        connection = None
        try:
            connection = self.connection_pool.get_connection()
            yield connection
        except Error as e:
            logger.error(f"数据库连接错误: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """执行查询并返回结果"""
        with self.get_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(query, params)
                return cursor.fetchall()
            finally:
                cursor.close()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新操作并返回影响的行数"""
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, params)
                connection.commit()
                return cursor.rowcount
            finally:
                cursor.close()
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """批量执行操作"""
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.executemany(query, params_list)
                connection.commit()
                return cursor.rowcount
            finally:
                cursor.close()
    
    def init_database(self):
        """初始化数据库表结构"""
        try:
            self._create_tables()
            self._insert_default_data()
            logger.info("数据库表结构初始化完成")
        except Error as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _create_tables(self):
        """创建数据库表"""
        
        # 创建Lark机器人表
        create_bots_table = """
        CREATE TABLE IF NOT EXISTS lark_bots (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            webhook_url TEXT NOT NULL,
            timeout INT DEFAULT 10,
            retry_count INT DEFAULT 3,
            is_custom BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_is_custom (is_custom),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # 创建项目映射表
        create_mappings_table = """
        CREATE TABLE IF NOT EXISTS project_mappings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_name VARCHAR(100) NOT NULL UNIQUE,
            git_url TEXT,
            bot_id VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (bot_id) REFERENCES lark_bots(id) ON DELETE CASCADE,
            INDEX idx_project_name (project_name),
            INDEX idx_bot_id (bot_id),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # 创建配置历史表
        create_history_table = """
        CREATE TABLE IF NOT EXISTS config_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            operation_type ENUM('CREATE', 'UPDATE', 'DELETE') NOT NULL,
            table_name VARCHAR(50) NOT NULL,
            record_id VARCHAR(100) NOT NULL,
            old_data JSON,
            new_data JSON,
            operator VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_operation_type (operation_type),
            INDEX idx_table_name (table_name),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # 创建系统配置表
        create_system_config_table = """
        CREATE TABLE IF NOT EXISTS system_config (
            config_key VARCHAR(100) PRIMARY KEY,
            config_value JSON NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        tables = [
            create_bots_table,
            create_mappings_table,
            create_history_table,
            create_system_config_table
        ]
        
        for table_sql in tables:
            self.execute_update(table_sql)
    
    def _insert_default_data(self):
        """插入默认数据"""
        
        # 检查是否已有数据
        existing_bots = self.execute_query("SELECT COUNT(*) as count FROM lark_bots")
        if existing_bots[0]['count'] > 0:
            logger.info("数据库已有数据，跳过默认数据插入")
            return
        
        # 插入默认机器人
        default_bots = [
            ('default', '默认机器人', 'https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe', 10, 3, False),
            ('team_a', '团队A机器人', 'https://open.larksuite.com/open-apis/bot/v2/hook/team-a-webhook-id', 10, 3, False),
            ('team_b', '团队B机器人', 'https://open.larksuite.com/open-apis/bot/v2/hook/team-b-webhook-id', 10, 3, False)
        ]
        
        insert_bot_sql = """
        INSERT INTO lark_bots (id, name, webhook_url, timeout, retry_count, is_custom)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        self.execute_many(insert_bot_sql, default_bots)
        
        # 插入默认项目映射
        default_mappings = [
            ('jacocotest', 'https://gitlab.complexdevops.com/kian/jacocoTest.git', 'default'),
            ('project-a', 'http://git.example.com/project-a.git', 'team_a'),
            ('project-b', 'http://git.example.com/project-b.git', 'team_b')
        ]
        
        insert_mapping_sql = """
        INSERT INTO project_mappings (project_name, git_url, bot_id)
        VALUES (%s, %s, %s)
        """
        
        self.execute_many(insert_mapping_sql, default_mappings)
        
        # 插入系统配置
        system_configs = [
            ('admin_password_hash', '"5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"', '管理员密码哈希值'),
            ('default_scan_config', json.dumps({
                "maven_goals": ["clean", "test", "jacoco:report"],
                "use_docker": True,
                "force_local_scan": False,
                "scan_timeout": 1800,
                "enable_notifications": True
            }), '默认扫描配置'),
            ('database_version', '"1.0.0"', '数据库版本')
        ]
        
        insert_config_sql = """
        INSERT INTO system_config (config_key, config_value, description)
        VALUES (%s, %s, %s)
        """
        
        self.execute_many(insert_config_sql, system_configs)
        
        logger.info("默认数据插入完成")
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result is not None
        except Error as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        try:
            info = {}
            
            # 数据库版本
            version_result = self.execute_query("SELECT VERSION() as version")
            info['mysql_version'] = version_result[0]['version'] if version_result else 'Unknown'
            
            # 表统计
            tables_result = self.execute_query("""
                SELECT table_name, table_rows, data_length, index_length
                FROM information_schema.tables
                WHERE table_schema = %s
            """, (self.config['database'],))

            info['tables'] = {}
            for table in tables_result:
                table_name = table.get('table_name', table.get('TABLE_NAME', 'unknown'))
                table_rows = table.get('table_rows', table.get('TABLE_ROWS', 0))
                data_length = table.get('data_length', table.get('DATA_LENGTH', 0))
                index_length = table.get('index_length', table.get('INDEX_LENGTH', 0))

                info['tables'][table_name] = {
                    'rows': table_rows or 0,
                    'data_size': data_length or 0,
                    'index_size': index_length or 0
                }
            
            # 连接池状态
            info['connection_pool'] = {
                'pool_name': self.config['pool_name'],
                'pool_size': self.config['pool_size']
            }
            
            return info
            
        except Error as e:
            logger.error(f"获取数据库信息失败: {e}")
            return {'error': str(e)}

# 全局数据库管理器实例
db_manager = None

def init_database():
    """初始化数据库"""
    global db_manager
    try:
        db_manager = DatabaseManager()
        db_manager.init_database()
        logger.info("数据库初始化成功")
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    global db_manager
    if db_manager is None:
        init_database()
    return db_manager
