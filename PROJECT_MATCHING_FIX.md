# 项目机器人匹配问题修复

## 🎯 问题描述

您在前端config页面配置了`http://172.16.1.30/kian/backend-lotto-game.git`项目使用特定的机器人，但推送时仍然使用默认机器人。

## 🔍 问题根本原因

系统存在**两套配置系统**，但项目匹配逻辑只使用了其中一套：

### 1. 文件配置系统
- 位置: `config/config.py`
- 存储: `PROJECT_BOT_MAPPING` 字典
- 用途: 静态配置和回退方案

### 2. MySQL配置系统  
- 位置: `src/mysql_config_manager.py`
- 存储: MySQL数据库表
- 用途: 动态配置（前端页面配置）

### 问题所在
`get_bot_for_project()` 函数只检查文件配置，**完全忽略了MySQL配置**！

这导致：
- ✅ 前端页面能正确保存配置到MySQL
- ❌ 但webhook处理时只读取文件配置
- ❌ 结果：总是使用默认机器人

## 🔧 已实施的修复

### 1. 修复项目匹配逻辑

修改了 `config/config.py` 中的 `get_bot_for_project()` 函数：

```python
def get_bot_for_project(repo_url: str, project_name: str) -> str:
    """根据项目信息匹配对应的机器人ID"""
    import os
    
    # 检查是否使用MySQL配置
    config_storage_type = os.getenv('CONFIG_STORAGE_TYPE', 'file')
    
    if config_storage_type == 'mysql':
        try:
            from src.mysql_config_manager import get_mysql_config_manager
            mysql_manager = get_mysql_config_manager()
            
            # 1. 首先检查MySQL中的项目映射
            project_mappings = mysql_manager.get_project_mappings()
            if project_name in project_mappings:
                return project_mappings[project_name]
            
            # 2. 检查MySQL中的通配符匹配
            for pattern, bot_id in project_mappings.items():
                if '*' in pattern:
                    regex_pattern = pattern.replace('*', '.*')
                    if re.match(f"^{regex_pattern}$", project_name):
                        return bot_id
            
        except Exception as e:
            logger.warning(f"MySQL配置查询失败，回退到文件配置: {e}")

    # 文件配置系统（回退方案）
    # ... 原有逻辑保持不变
```

### 2. 修复机器人配置获取

修改了 `get_lark_config()` 函数：

```python
def get_lark_config(bot_id: str) -> Dict[str, Any]:
    """获取指定机器人的配置"""
    import os
    
    # 检查是否使用MySQL配置
    config_storage_type = os.getenv('CONFIG_STORAGE_TYPE', 'file')
    
    if config_storage_type == 'mysql':
        try:
            from src.mysql_config_manager import get_mysql_config_manager
            mysql_manager = get_mysql_config_manager()
            
            # 从MySQL获取机器人配置
            lark_bots = mysql_manager.get_lark_bots()
            if bot_id in lark_bots:
                return lark_bots[bot_id]
            elif "default" in lark_bots:
                return lark_bots["default"]
            
        except Exception as e:
            logger.warning(f"MySQL机器人配置查询失败，回退到文件配置: {e}")
    
    # 文件配置系统（回退方案）
    return LARK_BOTS.get(bot_id, LARK_BOTS["default"])
```

## ✅ 修复效果

### 配置优先级（从高到低）：
1. **MySQL数据库配置**（前端页面配置）
2. **文件配置**（静态配置，回退方案）
3. **默认机器人**（最后的回退）

### 匹配逻辑：
1. **精确匹配**: 项目名称完全匹配
2. **通配符匹配**: 支持 `*` 通配符模式
3. **URL路径匹配**: 支持URL路径模式匹配
4. **默认回退**: 如果都不匹配，使用默认机器人

## 🚀 验证步骤

### 1. 重启服务
```bash
# Linux环境
sudo systemctl restart jacoco-api
# 或
pkill -f 'python.*app.py'
python3 app.py &
```

### 2. 确认环境变量
```bash
export CONFIG_STORAGE_TYPE=mysql
export MYSQL_HOST=172.16.1.30
export MYSQL_USER=jacoco
export MYSQL_PASSWORD=asd301325..
```

### 3. 测试推送
在GitLab中推送代码到 `backend-lotto-game` 项目

### 4. 预期结果
- ✅ 使用您在前端配置的机器人（而不是默认机器人）
- ✅ 发送到正确的Lark群组
- ✅ 通知内容显示正确的机器人名称

## 🔍 故障排除

### 如果仍然使用默认机器人：

1. **检查环境变量**:
```bash
echo $CONFIG_STORAGE_TYPE  # 应该是 mysql
```

2. **检查MySQL连接**:
```bash
mysql -h 172.16.1.30 -u jacoco -p jacoco_config
```

3. **检查项目配置**:
访问 `http://localhost:8002/config` 确认项目映射存在

4. **查看日志**:
```bash
tail -f logs/jacoco-api.log
# 查找 "MySQL配置查询失败" 等错误信息
```

### 如果MySQL查询失败：

系统会自动回退到文件配置，这时：
- 检查 `config/config.py` 中的 `PROJECT_BOT_MAPPING`
- 手动添加项目映射：
```python
PROJECT_BOT_MAPPING = {
    "backend-lotto-game": "your_bot_id",
    # ... 其他映射
}
```

## 📋 总结

### ✅ 已修复的问题：
1. **配置系统统一**: 现在优先使用MySQL配置
2. **前端配置生效**: 前端页面的配置现在会被正确使用
3. **回退机制**: 如果MySQL失败，自动回退到文件配置
4. **兼容性**: 保持与现有配置的完全兼容

### 🎯 核心改进：
- **智能配置选择**: 根据环境变量自动选择配置源
- **优雅降级**: MySQL失败时自动回退，不影响服务
- **完整支持**: 支持精确匹配、通配符匹配等所有功能

现在您的 `backend-lotto-game` 项目应该正确使用您在前端配置的机器人了！🚀
