# 通用 JaCoCo 覆盖率扫描服务

**🚀 支持任何配置了 webhook 的 Maven 项目的自动化 JaCoCo 覆盖率扫描服务**

基于 Docker 容器的通用 Git webhook 接收接口，**无需为每个项目单独配置**，**支持 GitHub 和 GitLab**，**无需修改原始 Java 项目的 pom.xml 文件**。

## 📋 项目特色

### 🌟 **通用性**
- ✅ **零配置**: 任何 Maven 项目都可以直接使用，无需预先配置
- ✅ **自动识别**: 自动从 webhook 中提取项目信息并生成配置
- ✅ **多平台支持**: 同时支持 GitHub、GitLab、GitLab CE/EE
- ✅ **智能适配**: 自动适配不同的 Git 服务器和项目结构

### 🎯 **主要功能**
1. **接收任何 Git 仓库的 webhook 事件** (GitHub/GitLab)
2. **自动触发 Java Maven 项目的 JaCoCo 覆盖率扫描**
3. **在 Docker 容器中隔离执行扫描**，避免污染主机环境
4. **生成多格式的覆盖率报告** (XML、HTML、JSON)
5. **自动发送飞书通知**，实时反馈扫描结果
6. **增量代码更新**，提高扫描效率

### 🎯 适用场景

- **企业级 CI/CD**: 为所有 Maven 项目提供统一的覆盖率扫描服务
- **多项目管理**: 无需为每个项目单独配置，一个服务支持所有项目
- **代码质量监控**: 持续跟踪所有项目的测试覆盖率变化
- **团队协作**: 为开发团队提供实时的代码质量反馈
- **快速集成**: 新项目只需配置 webhook 即可立即使用

## 🔧 主要功能

### 1. 多平台 Webhook 支持
- **GitHub**: 完整支持 GitHub webhook 格式和签名验证
- **GitLab**: 完整支持 GitLab webhook 格式和 Token 验证
- **自动识别**: 根据 webhook 内容自动识别来源平台

### 2. Docker 化 JaCoCo 扫描
- **隔离环境**: 在独立的 Docker 容器中执行扫描
- **无侵入性**: 不修改原始项目的 pom.xml 文件
- **动态配置**: 使用外部 Maven 配置文件注入 JaCoCo 插件
- **多格式报告**: 生成 XML、HTML、JSON 格式的覆盖率报告

### 3. 增量更新机制
- **首次克隆**: 第一次扫描时完整克隆仓库
- **增量更新**: 后续扫描使用 `git pull` 获取最新代码
- **持久化存储**: 本地保存仓库副本，提高扫描效率
- **智能切换**: 自动处理分支切换和提交检出

### 4. 飞书机器人通知
- **实时通知**: 扫描完成后自动发送覆盖率报告到飞书群聊
- **富文本消息**: 支持卡片式消息，包含覆盖率图表和详细数据
- **错误通知**: 扫描失败时发送错误信息到飞书
- **可配置**: 支持为不同项目配置不同的飞书机器人

### 5. 异步任务处理
- **Celery 队列**: 使用 Celery 进行异步任务处理
- **Redis 支持**: 基于 Redis 的任务队列和结果存储
- **任务跟踪**: 提供任务 ID 用于跟踪扫描进度

### 6. RESTful API
- **标准接口**: 提供标准的 REST API 接口
- **文档完整**: 内置 Swagger UI 和 ReDoc 文档
- **易于集成**: 可轻松集成到现有的 CI/CD 系统中

## 🎯 核心特性

- ✅ **多平台支持**: 支持 GitHub 和 GitLab webhook
- ✅ **无侵入性**: 不修改原始项目的 pom.xml 文件
- ✅ **Docker 隔离**: 在独立的 Docker 容器中执行扫描
- ✅ **外部配置**: 使用外部 Maven 配置文件添加 JaCoCo 插件
- ✅ **自动化**: 通过 Git webhook 自动触发
- ✅ **多格式报告**: 生成 XML、HTML 和 JSON 格式的报告
- ✅ **实时处理**: 支持异步任务队列处理

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 确保 Docker 已安装并运行
docker --version
```

### 2. 构建 Docker 镜像

```bash
# Linux/Mac
./build-docker.sh

# Windows
.\build-docker.bat

# 或手动构建
docker build -t jacoco-scanner:latest -f docker/Dockerfile.jacoco-scanner .
```

### 3. 启动服务

```bash
# Windows
quick_start.bat

# Linux/Mac
./quick_start.sh

# 或手动启动
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### 4. 配置 Git Webhook

#### GitHub Webhook
- URL: `http://your-server:8001/github/webhook`
- Content type: `application/json`
- Secret: 在 `.env` 文件中配置
- 事件: 选择 "Push events"

#### GitLab Webhook
- URL: `http://your-server:8001/github/webhook`
- Content type: `application/json`
- Secret Token: 在 `.env` 文件中配置
- 触发器: 选择 "Push events"

## 📁 项目结构

```text
jacocoApi/
├── 📄 核心应用文件
│   ├── main.py                      # 主 FastAPI 应用
│   ├── github_webhook.py            # Git webhook 处理器 (支持 GitHub/GitLab)
│   ├── jacoco_tasks.py              # Docker 扫描任务
│   ├── config.py                    # 配置文件
│   ├── api_endpoints.py             # API 端点
│   ├── security.py                  # 安全模块
│   └── logging_config.py            # 日志配置
│
├── 🐳 Docker 相关
│   ├── docker/
│   │   ├── Dockerfile.jacoco-scanner # JaCoCo 扫描器镜像
│   │   └── scripts/                 # 扫描脚本
│   ├── build-docker.sh              # Linux/Mac Docker 构建脚本
│   └── build-docker.bat             # Windows Docker 构建脚本
│
├── ⚙️ 配置文件
│   ├── .env                         # 环境配置
│   ├── .env.example                 # 环境配置示例
│   ├── requirements.txt             # Python 依赖
│   └── maven-configs/               # Maven 配置模板
│       └── jacoco-pom-overlay.xml   # JaCoCo 配置覆盖
│
├── 🚀 启动脚本
│   ├── quick_start.bat              # Windows 快速启动
│   └── quick_start.sh               # Linux/Mac 快速启动
│
├── 🧪 测试文件
│   ├── test_github_webhook.py       # webhook 测试脚本
│   ├── test-docker-scan.py          # Docker 扫描测试
│   └── demo_test.py                 # 演示测试
│
└── 📝 文档
    └── README.md                    # 项目文档
```

## 🔧 配置

### 环境配置 (`.env`)

```env
# GitHub Webhook 密钥
GIT_WEBHOOK_SECRET=your_github_webhook_secret_here

# 调试模式
DEBUG=True

# Redis 配置 (用于 Celery)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 通用配置 (`config.py`)

**🎉 无需为每个项目单独配置！** 系统使用通用配置自动适配所有项目：

```python
# 通用扫描配置 - 适用于所有接收到webhook的项目
DEFAULT_SCAN_CONFIG = {
    "scan_method": "jacoco",
    "project_type": "maven",
    "docker_image": "jacoco-scanner:latest",
    "notification_webhook": "https://open.larksuite.com/open-apis/bot/v2/hook/57031f94-2e1a-473c-8efc-f371b648dfbe",
    "coverage_threshold": 50.0,
    "maven_goals": ["clean", "test", "jacoco:report"],
    "report_formats": ["xml", "html", "json"],
    "use_docker": True,
    "use_incremental_update": True,
    "scan_timeout": 1800,
    "max_retries": 3,
}

# 可选：特定项目的自定义配置
CUSTOM_PROJECT_CONFIG = {
    # 如果某个项目需要特殊配置，可以在这里添加
    # "project-name": {
    #     "notification_webhook": "https://custom-webhook-url",
    #     "coverage_threshold": 80.0,
    # }
}
```

**✨ 自动功能**:
- 🔄 **自动项目识别**: 从 webhook 中提取项目名称
- 📁 **自动路径生成**: 根据项目名称生成本地存储路径
- ⚙️ **智能配置**: 自动应用通用配置，支持项目特定覆盖

## 🌐 API 接口详情

### 接口总览

| 方法 | 路径 | 用途 | 认证 |
|------|------|------|------|
| POST | `/github/webhook` | 接收 Git webhook 事件 | 签名验证 |
| POST | `/github/webhook-no-auth` | 测试用 webhook 接收 | 无需认证 |
| GET | `/health` | 系统健康检查 | 无需认证 |
| GET | `/github/test` | Webhook 连通性测试 | 无需认证 |
| GET | `/docs` | Swagger UI 文档 | 无需认证 |
| GET | `/redoc` | ReDoc 文档 | 无需认证 |
| GET | `/openapi.json` | OpenAPI 规范 | 无需认证 |

### 核心接口

#### 1. Webhook 接收接口
- **`POST /github/webhook`** - 主要的 Git webhook 接收接口
  - **用途**: 接收来自 GitHub 或 GitLab 的 webhook 事件
  - **支持格式**: GitHub webhook 格式、GitLab webhook 格式
  - **认证**: 支持签名验证 (GitHub HMAC-SHA256, GitLab Token)
  - **功能**: 自动解析事件，触发 JaCoCo 扫描任务
  - **返回**: 任务ID和处理状态

- **`POST /github/webhook-no-auth`** - 无认证测试接口
  - **用途**: 用于测试和调试，跳过签名验证
  - **支持格式**: 同上
  - **认证**: 无需认证
  - **功能**: 同主接口，但用于开发测试

#### 2. 系统监控接口
- **`GET /health`** - 系统健康检查
  - **用途**: 检查服务运行状态
  - **返回**: 服务状态、版本信息、时间戳

- **`GET /github/test`** - Webhook 连通性测试
  - **用途**: 测试 webhook 端点是否正常工作
  - **返回**: 测试成功消息

#### 3. API 文档接口
- **`GET /docs`** - Swagger UI 文档
  - **用途**: 交互式 API 文档界面
  - **功能**: 可直接测试 API 接口

- **`GET /redoc`** - ReDoc 文档
  - **用途**: 另一种风格的 API 文档

- **`GET /openapi.json`** - OpenAPI 规范
  - **用途**: 获取 API 的 OpenAPI 3.0 规范文件

### API 响应格式

#### 成功响应示例
```json
{
  "status": "accepted",
  "task_id": "task_12345",
  "request_id": "req_67890",
  "message": "JaCoCo 扫描任务已成功排队",
  "extracted_info": {
    "repo_url": "https://github.com/user/project.git",
    "commit_id": "abc123def456",
    "branch_name": "main",
    "service_name": "my-project"
  }
}
```

#### 错误响应示例
```json
{
  "status": "error",
  "message": "签名验证失败",
  "detail": "Invalid webhook signature"
}
```

## 🔄 工作流程

1. **Git Push** → webhook 发送到 API (支持 GitHub/GitLab)
2. **事件解析** → 自动识别 GitHub 或 GitLab 格式
3. **任务排队** → Celery 将扫描任务加入队列
4. **Docker 启动** → 启动 JaCoCo 扫描容器
5. **仓库克隆** → 在容器内克隆指定提交
6. **POM 合并** → 动态合并原始 pom.xml 与 JaCoCo 配置
7. **执行扫描** → 运行 `mvn clean test jacoco:report`
8. **报告生成** → 生成 XML、HTML 和 JSON 报告
9. **结果返回** → 解析报告并返回覆盖率数据

## 📊 报告格式

- **XML 报告**: 标准 JaCoCo XML 格式
- **HTML 报告**: 可视化的网页报告
- **JSON 摘要**: 结构化的覆盖率数据

## 🧪 测试

```bash
# 测试 GitHub webhook
python test_github_webhook.py

# 测试 Docker 扫描
python test-docker-scan.py

# 演示测试
python demo_test.py

# 健康检查
curl http://localhost:8001/health

# 测试 webhook 端点
curl http://localhost:8001/github/test
```

## � 使用示例

### GitHub Webhook 示例

```json
{
  "ref": "refs/heads/main",
  "repository": {
    "name": "my-java-project",
    "clone_url": "https://github.com/user/my-java-project.git"
  },
  "commits": [{
    "id": "abc123def456",
    "message": "Add new feature"
  }],
  "after": "abc123def456"
}
```

### GitLab Webhook 示例

```json
{
  "object_kind": "push",
  "ref": "refs/heads/main",
  "user_name": "developer",
  "project": {
    "name": "my-java-project",
    "http_url": "https://gitlab.com/user/my-java-project.git"
  },
  "commits": [{
    "id": "abc123def456",
    "message": "Add new feature"
  }]
}
```

## 🔧 系统要求

- Python 3.8+
- Docker
- Redis (用于 Celery)
- Java 11+ (在 Docker 容器中)
- Maven 3.6+ (在 Docker 容器中)

## 🎉 功能状态

✅ **多平台支持**: GitHub 和 GitLab webhook
✅ **服务运行**: 端口 8001
✅ **Docker 扫描器**: 已配置并可用
✅ **无侵入性**: 不修改原始 pom.xml
✅ **实时处理**: 支持异步任务队列

## 📖 API 文档

启动服务后，访问以下地址查看详细的 API 文档：

- **Swagger UI**: <http://localhost:8001/docs>
- **ReDoc**: <http://localhost:8001/redoc>
- **OpenAPI JSON**: <http://localhost:8001/openapi.json>

## 🔧 故障排除

### 常见问题

1. **Docker 镜像构建失败**
   ```bash
   # 检查 Docker 是否运行
   docker --version

   # 重新构建镜像
   docker build -t jacoco-scanner:latest -f docker/Dockerfile.jacoco-scanner .
   ```

2. **Webhook 接收失败**
   ```bash
   # 检查服务状态
   curl http://localhost:8001/health

   # 使用无认证端点测试
   curl -X POST http://localhost:8001/github/webhook-no-auth \
     -H "Content-Type: application/json" \
     -d '{"object_kind": "push", "ref": "refs/heads/main"}'
   ```

3. **JaCoCo 扫描失败**
   ```bash
   # 检查 Docker 镜像
   docker images jacoco-scanner

   # 查看容器日志
   docker logs <container_id>
   ```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 📄 许可证

本项目采用 MIT 许可证。
