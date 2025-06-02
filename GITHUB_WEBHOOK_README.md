# GitHub Webhook JaCoCo 覆盖率统计 API

这是一个专门用于接收 GitHub webhook 并触发 JaCoCo 覆盖率统计的 Python API 服务。当您向 GitHub 提交代码时，GitHub 会发送 webhook 消息给这个 API，然后 API 会自动执行 JaCoCo 覆盖率统计并生成报告。

## 功能特性

- 🔗 **GitHub Webhook 集成**: 自动接收 GitHub 的 push 和 pull request 事件
- 📊 **JaCoCo 覆盖率统计**: 自动运行 Maven 测试并生成 JaCoCo 覆盖率报告
- 🔐 **安全验证**: 支持 GitHub webhook 签名验证
- 📈 **实时监控**: 提供 Prometheus 指标和健康检查端点
- 🚀 **异步处理**: 使用 Celery 进行后台任务处理
- 📝 **详细日志**: 完整的操作日志记录
- 🌐 **RESTful API**: 提供完整的 REST API 接口

## 系统要求

- Python 3.8+
- Redis (用于 Celery 消息队列)
- Java 11+ (用于运行 Maven 项目)
- Maven 3.6+ (用于构建和测试)
- Git (用于克隆仓库)

## 安装和配置

### 1. 安装依赖

```bash
cd Script/GE/jacocoApi
pip install -r requirements.txt
```

### 2. 启动 Redis

确保 Redis 服务正在运行：

```bash
# Windows (如果使用 WSL 或安装了 Redis)
redis-server

# 或者使用 Docker
docker run -d -p 6379:6379 redis:alpine
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# GitHub Webhook 密钥
GIT_WEBHOOK_SECRET=your_github_webhook_secret

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API 配置
DEBUG=True
LOG_LEVEL=INFO

# 速率限制
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=3600
```

### 4. 配置项目

在 `config.py` 中添加您的 GitHub 仓库配置：

```python
SERVICE_CONFIG = {
    "https://github.com/your-username/your-repo.git": {
        "service_name": "your-service",
        "scan_method": "jacoco",
        "project_type": "maven",
        "notification_webhook": "your_notification_url",
        "coverage_threshold": 50.0,
        "maven_goals": ["clean", "test", "jacoco:report"],
        "report_formats": ["xml", "html"],
    }
}
```

## 使用方法

### 1. 启动服务

使用提供的启动脚本：

```bash
python start_github_webhook.py
```

或者手动启动：

```bash
# 启动 Celery worker
celery -A jacoco_tasks.celery_app worker --loglevel=info

# 启动 FastAPI 服务器
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 配置 GitHub Webhook

1. 在您的 GitHub 仓库中，转到 Settings > Webhooks
2. 点击 "Add webhook"
3. 设置 Payload URL: `http://your-server:8000/github/webhook`
4. 设置 Content type: `application/json`
5. 设置 Secret: 与 `.env` 文件中的 `GIT_WEBHOOK_SECRET` 相同
6. 选择事件: 至少选择 "Push" 事件
7. 确保 webhook 是 Active 状态

### 3. 测试 Webhook

使用提供的测试脚本：

```bash
python test_github_webhook.py --url http://localhost:8000 --secret your_github_webhook_secret
```

## API 端点

### GitHub Webhook 端点

- `POST /github/webhook` - 接收 GitHub webhook 事件
- `GET /github/test` - 测试端点

### 通用 API 端点

- `GET /health` - 健康检查
- `GET /docs` - API 文档 (Swagger UI)
- `GET /metrics` - Prometheus 指标
- `GET /task/{task_id}` - 查询任务状态

### API 端点 (需要 API 密钥)

- `POST /api/scan` - 手动触发扫描
- `GET /api/task/{task_id}` - 查询任务状态

## JaCoCo 报告

当扫描完成后，系统会生成以下报告：

1. **XML 报告**: `target/site/jacoco/jacoco.xml`
2. **HTML 报告**: `target/site/jacoco/index.html`
3. **覆盖率数据**: 通过 API 返回的 JSON 格式数据

### 报告内容包括

- 总体行覆盖率百分比
- 分支覆盖率百分比
- 覆盖的行数和总行数
- 包级别的覆盖率详情
- HTML 可视化报告

## 工作流程

1. **接收 Webhook**: GitHub 发送 push 事件到 `/github/webhook`
2. **验证签名**: 验证 GitHub webhook 签名确保安全性
3. **解析事件**: 提取仓库 URL、提交 ID 和分支信息
4. **查找配置**: 根据仓库 URL 查找对应的服务配置
5. **排队任务**: 将扫描任务添加到 Celery 队列
6. **克隆仓库**: 在临时目录中克隆指定的提交
7. **运行测试**: 执行 `mvn clean test jacoco:report`
8. **解析报告**: 解析生成的 JaCoCo XML 报告
9. **返回结果**: 返回覆盖率统计结果
10. **发送通知**: (可选) 发送结果到配置的 webhook

## 监控和日志

### 日志文件

- `logs/jacoco_api.log` - 应用日志
- `logs/jacoco_api_error.log` - 错误日志

### Prometheus 指标

访问 `http://localhost:8000/metrics` 查看指标：

- `webhook_requests_total` - Webhook 请求总数
- `scan_duration_seconds` - 扫描持续时间

### 健康检查

访问 `http://localhost:8000/health` 检查服务状态。

## 故障排除

### 常见问题

1. **Redis 连接失败**
   - 确保 Redis 服务正在运行
   - 检查 Redis 连接配置

2. **Maven 执行失败**
   - 确保 Java 和 Maven 已安装并在 PATH 中
   - 检查项目的 pom.xml 配置

3. **Git 克隆失败**
   - 确保有访问仓库的权限
   - 检查网络连接

4. **JaCoCo 报告未生成**
   - 确保 pom.xml 中包含 JaCoCo 插件配置
   - 检查测试是否正常运行

### 调试模式

设置环境变量 `DEBUG=True` 启用详细日志。

## 安全注意事项

1. **Webhook 密钥**: 始终使用强密钥并定期更换
2. **网络访问**: 限制 API 服务器的网络访问
3. **日志安全**: 确保日志文件不包含敏感信息
4. **权限控制**: 使用最小权限原则

## 扩展和自定义

### 添加新的项目类型

在 `jacoco_tasks.py` 中添加对其他构建工具的支持（如 Gradle）。

### 自定义通知

修改 `_send_notification` 函数以支持不同的通知方式。

### 添加更多指标

在 Prometheus 指标中添加更多监控数据。

## 许可证

本项目使用 MIT 许可证。
