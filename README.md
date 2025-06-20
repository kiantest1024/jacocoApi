# JaCoCo API 覆盖率扫描系统

基于 Docker 和本地 Maven 的 Java 项目代码覆盖率扫描 API 服务。

## 功能特性

- 🐳 **Docker 扫描**: 隔离环境，支持复杂项目依赖
- 🏠 **本地扫描**: 快速扫描，适合简单项目
- 🔧 **智能修复**: 自动检测和修复项目依赖问题
- 📊 **多格式报告**: XML 和 HTML 格式的覆盖率报告
- 🔔 **通知集成**: 支持 Lark 机器人通知
- 🎯 **现代测试框架**: 支持 JUnit 5、Mockito、AssertJ
- 🔍 **调试模式**: 详细的构建日志和扫描过程跟踪

## 快速开始

### 1. 环境要求

- Python 3.6+
- Docker (推荐)
- Maven 3.6+ (本地扫描)
- Java 11+

### 2. 启动服务

#### 正常版本
```bash
python app.py
```
服务将在 `http://localhost:8002` 启动。

#### 调试版本
```bash
# Linux/macOS
./start_debug.sh

# Windows
start_debug.bat

# 或手动启动
python app_debug.py
```
调试服务将在 `http://localhost:8003` 启动，提供详细的扫描日志。

### 3. 发送扫描请求

```bash
# 正常版本
curl -X POST http://localhost:8002/github/webhook-no-auth \
  -H "Content-Type: application/json" \
  -d '{
    "object_kind": "push",
    "project": {
      "name": "your-project",
      "http_url": "http://your-git-server/project.git"
    },
    "commits": [{"id": "main"}],
    "ref": "refs/heads/main"
  }'

# 调试版本 (端口 8003)
curl -X POST http://localhost:8003/github/webhook-no-auth \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## 版本对比

| 功能 | 正常版本 | 调试版本 |
|------|----------|----------|
| 端口 | 8002 | 8003 |
| 日志级别 | INFO | DEBUG |
| 日志文件 | 无 | jacoco_debug.log |
| Maven 输出 | 简化 | 完整显示 |
| 构建过程 | 基本信息 | 详细步骤 |
| 错误信息 | 基本 | 详细堆栈 |
| 性能监控 | 无 | 执行时间 |
| 调试接口 | 无 | /debug/logs |

## 项目结构

```
jacocoApi/
├── app.py                    # 正常版本应用
├── app_debug.py              # 调试版本应用
├── start_debug.sh            # Linux/macOS 调试启动脚本
├── start_debug.bat           # Windows 调试启动脚本
├── DEBUG_README.md           # 调试版本详细说明
├── src/                      # 源代码
│   ├── jacoco_tasks.py       # 正常扫描任务
│   ├── jacoco_tasks_debug.py # 调试扫描任务
│   ├── lark_notification.py  # 通知功能
│   └── utils.py              # 工具函数
├── config/                   # 配置文件
│   └── config.py             # 项目配置
├── docker/                   # Docker 相关
│   ├── Dockerfile.alpine     # Docker 镜像定义
│   └── scripts/              # 扫描脚本
├── tools/                    # 工具脚本
│   ├── build.sh              # 构建工具
│   └── fix-dependencies.py   # 依赖修复工具
├── quick-test.sh             # 功能验证脚本
├── diagnose.py               # 诊断工具
└── README.md                 # 本文档
```

## 调试功能详解

### 详细日志输出

调试版本会记录：
- Maven 命令的完整输出
- 每个构建步骤的执行时间
- 项目结构分析结果
- 测试执行统计信息
- 编译错误和警告详情

### 调试接口

- **GET /debug/logs**: 获取最近的调试日志
- **GET /health**: 健康检查（包含调试信息）
- **GET /**: 根路径（显示调试模式状态）

### 日志文件

调试版本会生成 `jacoco_debug.log` 文件，包含：
- 详细的请求处理过程
- Maven 命令执行日志
- 错误堆栈跟踪
- 性能监控数据

## 工具使用

### 构建 Docker 镜像

```bash
./tools/build.sh
```

### 验证功能

```bash
./quick-test.sh
```

### 诊断问题

```bash
python diagnose.py
```

### 修复项目依赖

```bash
python tools/fix-dependencies.py /path/to/project
```

## 配置说明

### 项目配置

在 `config/config.py` 中配置项目特定的设置：

```python
PROJECT_CONFIGS = {
    "your-project-url": {
        "service_name": "your-service",
        "bot_id": "your-bot-id",
        "enable_notifications": True,
        "debug_mode": False,        # 正常版本
        "verbose_logging": False    # 正常版本
    }
}
```

调试版本会自动启用 `debug_mode` 和 `verbose_logging`。

### 扫描配置

```python
DEFAULT_SCAN_CONFIG = {
    "use_docker": True,           # 优先使用 Docker
    "timeout": 300,               # 扫描超时时间
    "enable_notifications": True, # 启用通知
    "force_local_scan": False,    # 强制本地扫描
    "debug_mode": False,          # 调试模式
    "verbose_logging": False      # 详细日志
}
```

## API 接口

### POST /github/webhook-no-auth

接收 Git webhook 并触发扫描。

**请求体**:
```json
{
  "object_kind": "push",
  "project": {
    "name": "project-name",
    "http_url": "git-repository-url"
  },
  "commits": [{"id": "commit-hash"}],
  "ref": "refs/heads/branch-name"
}
```

**正常版本响应**:
```json
{
  "status": "success",
  "message": "扫描已完成",
  "coverage": {
    "line": 85.5,
    "branch": 78.2,
    "instruction": 87.1
  }
}
```

**调试版本响应**:
```json
{
  "status": "completed",
  "request_id": "debug_req_1234567890",
  "message": "调试扫描完成 - 项目: test-project, 提交: abc12345",
  "debug_info": {
    "scan_method": "docker",
    "scan_analysis": {
      "tests_run": 15,
      "tests_failed": 0,
      "compilation_errors": [],
      "build_warnings": []
    },
    "service_config": {...},
    "reports_dir": "/tmp/jacoco_debug_reports_..."
  },
  "scan_result": {...},
  "report_data": {...}
}
```

## 故障排除

### 覆盖率为 0%

1. 运行诊断工具: `python diagnose.py`
2. 验证基本功能: `./quick-test.sh`
3. 使用调试版本查看详细日志
4. 检查项目是否有测试代码
5. 确认测试真正调用了主代码

### 调试版本特定问题

1. 查看调试日志: `tail -f jacoco_debug.log`
2. 访问调试接口: `http://localhost:8003/debug/logs`
3. 检查 Maven 输出中的错误信息
4. 分析项目结构检查结果

### Docker 构建失败

1. 检查 Docker 服务状态
2. 确保有足够的磁盘空间
3. 重新构建: `./tools/build.sh`

### 依赖问题

1. 使用依赖修复工具: `python tools/fix-dependencies.py <project-path>`
2. 检查 Maven 版本兼容性
3. 确认网络连接正常

## 支持的测试框架

- **JUnit 5** (Jupiter) - 现代 Java 测试框架
- **JUnit 4** - 向后兼容支持
- **Mockito** - Mock 对象框架
- **AssertJ** - 流畅断言库

## 许可证

MIT License
