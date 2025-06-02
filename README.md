# JaCoCo Webhook API

[English](#english) | [中文](#chinese)

<a id="english"></a>
## English

A FastAPI-based webhook receiver for triggering JaCoCo code coverage scans from Git repository events.

### Features

- Receives webhooks from multiple Git providers (GitHub, GitLab, Gitee)
- Validates webhook signatures for security
- Processes webhook payloads to extract repository and commit information
- Maps repositories to service configurations
- Queues scan tasks to Celery for asynchronous processing
- Provides health check endpoint
- Rate limiting to prevent abuse
- Task status tracking and monitoring
- Detailed logging with request IDs
- Configurable via environment variables
- Swagger UI documentation
- Docker-based JaCoCo scanning
- Incremental build support for faster scanning
- Dedicated API endpoints for direct scan triggering

### Prerequisites

- Python 3.8+
- Redis (for Celery task queue)

### Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the example:

```bash
cp .env.example .env
```

4. Edit the `.env` file to set your webhook secret and other configuration options.

<a id="chinese"></a>
## 中文

基于 FastAPI 的 Webhook 接收器，用于从 Git 仓库事件触发 JaCoCo 代码覆盖率扫描。

### 功能特点

- 接收来自多个 Git 提供商（GitHub、GitLab、Gitee）的 webhook
- 验证 webhook 签名以确保安全性
- 处理 webhook 负载以提取仓库和提交信息
- 将仓库映射到服务配置
- 将扫描任务排队到 Celery 进行异步处理
- 提供健康检查端点
- 速率限制以防止滥用
- 任务状态跟踪和监控
- 带有请求 ID 的详细日志记录
- 通过环境变量进行配置
- Swagger UI 文档
- 基于 Docker 的 JaCoCo 扫描
- 增量构建支持，加快扫描速度
- 专用 API 端点用于直接触发扫描

### 前提条件

- Python 3.8+
- Redis（用于 Celery 任务队列）

### 安装

1. 克隆仓库
2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 从示例创建 `.env` 文件：

```bash
cp .env.example .env
```

4. 编辑 `.env` 文件以设置您的 webhook 密钥和其他配置选项。

### Configuration

The application uses the following configuration sources:

1. Environment variables (loaded from `.env` file)
2. Service configuration in `config.py`

#### Environment Variables

The application can be configured using environment variables. See the `.env.example` file for all available options. Key configuration options include:

```env
# API settings
API_TITLE=JaCoCo Scan Trigger API
API_VERSION=1.0.0
DEBUG=False

# Security settings
GIT_WEBHOOK_SECRET=your_secure_webhook_secret
ALLOWED_ORIGINS=*

# Rate limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=3600

# Redis and Celery configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

#### Service Configuration

Edit the `SERVICE_CONFIG` dictionary in `config.py` to map your Git repository URLs to service-specific configurations:

```python
SERVICE_CONFIG = {
    "git@your-git-server.com:user/service-a.git": {
        "service_name": "service-a",
        "scan_method": "solution1",
        "notification_webhook": "http://your.lark.webhook.url/group_a",
        # ... other service-specific configurations
    },
    # Add more repositories as needed
}
```

### Running the Application

#### Build Docker Image

Before running the application, build the JaCoCo scanner Docker image:

```bash
# On Linux/macOS
./build_docker.sh

# On Windows
build_docker.bat
```

#### Development Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode

For production, it's recommended to use a proper ASGI server like Uvicorn or Hypercorn behind a reverse proxy like Nginx.

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Running Celery Worker

Start a Celery worker to process the scan tasks:

```bash
celery -A tasks.celery_app worker --loglevel=info
```

#### Using Docker Compose

You can also use Docker Compose to run the entire application stack:

```bash
docker-compose up -d
```

### Webhook Setup

#### GitHub

1. Go to your repository settings
2. Navigate to Webhooks
3. Add a new webhook:
   - Payload URL: `https://your-server.com/scan-trigger`
   - Content type: `application/json`
   - Secret: The same value as `GIT_WEBHOOK_SECRET` in your `.env` file
   - Events: Select "Just the push event"

#### GitLab

1. Go to your repository settings
2. Navigate to Webhooks
3. Add a new webhook:
   - URL: `https://your-server.com/scan-trigger`
   - Secret token: The same value as `GIT_WEBHOOK_SECRET` in your `.env` file
   - Trigger: Select "Push events"

#### Gitee

1. Go to your repository settings
2. Navigate to Webhooks/WebHooks
3. Add a new webhook:
   - URL: `https://your-server.com/scan-trigger`
   - Password: The same value as `GIT_WEBHOOK_SECRET` in your `.env` file
   - Events: Select "Push"

### API Endpoints

- `GET /health`: Health check endpoint
- `POST /scan-trigger`: Webhook endpoint for Git providers
- `GET /task/{task_id}`: Get status of a scan task
- `GET /docs`: Swagger UI documentation
- `GET /openapi.json`: OpenAPI schema
- `POST /api/scan`: Direct API endpoint to trigger a scan
- `GET /api/task/{task_id}`: Get status of a scan task (API key required)

### Customization

#### Scan Methods

The application now uses a Docker-based scanning approach with the following workflow:

1. Creates a unique working directory for each scan
2. Clones the repository with the specified commit
3. Copies the JaCoCo settings file
4. Runs the scan in a Docker container
5. Parses and returns the results

You can customize the scanning behavior by:

1. Modifying the `jacoco-settings.xml` file
2. Updating the Docker image in `jacoco-scanner/Dockerfile`
3. Implementing custom scanners in the `scanners` module

Example API request to trigger a scan:

```json
POST /api/scan
{
  "service": "betService",
  "git_repo": "https://github.com/xxx/repo.git",
  "branch": "main",
  "commit_id": "abc123",
  "options": {
    "incremental_build": true,
    "keep_workspace": false
  }
}
```

#### Notification

The application can send notifications about scan results to a webhook URL specified in the service configuration. Customize the notification payload in the `_send_notification` function in `tasks.py`.

The default implementation sends the following data:

```json
{
  "service_name": "service-a",
  "commit_id": "abcd1234",
  "branch_name": "main",
  "coverage_percentage": 85.2,
  "lines_covered": 1250,
  "lines_total": 1468,
  "status": "success",
  "scan_method": "solution1",
  "duration_seconds": 45.2,
  "timestamp": "2023-05-10T12:34:56.789Z",
  "request_id": "req_1683720896_123456789"
}
```

#### Rate Limiting

Rate limiting is enabled by default to prevent abuse. You can configure the rate limits in the `.env` file:

```env
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=3600
```

This limits each client IP to 100 requests per hour. Adjust these values based on your expected usage.

### 配置

应用程序使用以下配置源：

1. 环境变量（从 `.env` 文件加载）
2. `config.py` 中的服务配置

#### 环境变量

应用程序可以使用环境变量进行配置。有关所有可用选项，请参见 `.env.example` 文件。主要配置选项包括：

```env
# API 设置
API_TITLE=JaCoCo Scan Trigger API
API_VERSION=1.0.0
DEBUG=False

# 安全设置
GIT_WEBHOOK_SECRET=your_secure_webhook_secret
ALLOWED_ORIGINS=*

# 速率限制
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=3600

# Redis 和 Celery 配置
REDIS_HOST=localhost
REDIS_PORT=6379
```

#### 服务配置

编辑 `config.py` 中的 `SERVICE_CONFIG` 字典，将您的 Git 仓库 URL 映射到特定服务的配置：

```python
SERVICE_CONFIG = {
    "git@your-git-server.com:user/service-a.git": {
        "service_name": "service-a",
        "scan_method": "solution1",
        "notification_webhook": "http://your.lark.webhook.url/group_a",
        # ... 其他特定于服务的配置
    },
    # 根据需要添加更多仓库
}
```

### 运行应用程序

#### 构建 Docker 镜像

在运行应用程序之前，构建 JaCoCo 扫描器 Docker 镜像：

```bash
# 在 Linux/macOS 上
./build_docker.sh

# 在 Windows 上
build_docker.bat
```

#### 开发模式

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 生产模式

对于生产环境，建议使用适当的 ASGI 服务器（如 Uvicorn 或 Hypercorn）并在 Nginx 等反向代理后面运行。

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 运行 Celery Worker

启动 Celery worker 以处理扫描任务：

```bash
celery -A tasks.celery_app worker --loglevel=info
```

#### 使用 Docker Compose

您也可以使用 Docker Compose 运行整个应用程序堆栈：

```bash
docker-compose up -d
```

### Webhook 设置

#### GitHub

1. 转到您的仓库设置
2. 导航到 Webhooks
3. 添加新的 webhook：
   - 负载 URL：`https://your-server.com/scan-trigger`
   - 内容类型：`application/json`
   - 密钥：与您 `.env` 文件中的 `GIT_WEBHOOK_SECRET` 相同的值
   - 事件：选择"仅推送事件"

#### GitLab

1. 转到您的仓库设置
2. 导航到 Webhooks
3. 添加新的 webhook：
   - URL：`https://your-server.com/scan-trigger`
   - 密钥令牌：与您 `.env` 文件中的 `GIT_WEBHOOK_SECRET` 相同的值
   - 触发器：选择"推送事件"

#### Gitee

1. 转到您的仓库设置
2. 导航到 Webhooks/WebHooks
3. 添加新的 webhook：
   - URL：`https://your-server.com/scan-trigger`
   - 密码：与您 `.env` 文件中的 `GIT_WEBHOOK_SECRET` 相同的值
   - 事件：选择"Push"

### API 端点

- `GET /health`：健康检查端点
- `POST /scan-trigger`：Git 提供商的 webhook 端点
- `GET /task/{task_id}`：获取扫描任务的状态
- `GET /docs`：Swagger UI 文档
- `GET /openapi.json`：OpenAPI 架构
- `POST /api/scan`：直接触发扫描的 API 端点
- `GET /api/task/{task_id}`：获取扫描任务的状态（需要 API 密钥）

### 自定义

#### 扫描方法

应用程序现在使用基于 Docker 的扫描方法，工作流程如下：

1. 为每次扫描创建唯一的工作目录
2. 克隆指定提交的仓库
3. 复制 JaCoCo 设置文件
4. 在 Docker 容器中运行扫描
5. 解析并返回结果

您可以通过以下方式自定义扫描行为：

1. 修改 `jacoco-settings.xml` 文件
2. 更新 `jacoco-scanner/Dockerfile` 中的 Docker 镜像
3. 在 `scanners` 模块中实现自定义扫描器

触发扫描的 API 请求示例：

```json
POST /api/scan
{
  "service": "betService",
  "git_repo": "https://github.com/xxx/repo.git",
  "branch": "main",
  "commit_id": "abc123",
  "options": {
    "incremental_build": true,
    "keep_workspace": false
  }
}
```

#### 通知

应用程序可以将有关扫描结果的通知发送到服务配置中指定的 webhook URL。在 `tasks.py` 中的 `_send_notification` 函数中自定义通知负载。

默认实现发送以下数据：

```json
{
  "service_name": "service-a",
  "commit_id": "abcd1234",
  "branch_name": "main",
  "coverage_percentage": 85.2,
  "lines_covered": 1250,
  "lines_total": 1468,
  "status": "success",
  "scan_method": "solution1",
  "duration_seconds": 45.2,
  "timestamp": "2023-05-10T12:34:56.789Z",
  "request_id": "req_1683720896_123456789"
}
```

#### 速率限制

默认启用速率限制以防止滥用。您可以在 `.env` 文件中配置速率限制：

```env
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=3600
```

这将每个客户端 IP 限制为每小时 100 个请求。根据您的预期使用情况调整这些值。
