# GitHub Webhook JaCoCo 覆盖率统计 API

基于 Docker 容器的 GitHub webhook 接收接口，用于自动触发 JaCoCo 覆盖率统计。**无需修改原始 Java 项目的 pom.xml 文件**。

## 🎯 核心特性

- ✅ **无侵入性**: 不修改原始项目的 pom.xml 文件
- ✅ **Docker 隔离**: 在独立的 Docker 容器中执行扫描
- ✅ **外部配置**: 使用外部 Maven 配置文件添加 JaCoCo 插件
- ✅ **自动化**: 通过 GitHub webhook 自动触发
- ✅ **多格式报告**: 生成 XML、HTML 和 JSON 格式的报告

## 🚀 快速开始

### 1. 启动服务

```bash
# Windows
quick_start.bat

# Linux/Mac
./quick_start.sh

# 或手动启动
python start_github_webhook.py
```

### 2. 构建 Docker 镜像

```bash
./build-docker.sh
```

### 3. 配置 GitHub Webhook

- URL: `http://your-server:8001/github/webhook`
- Content type: `application/json`
- Secret: 在 `.env` 文件中配置
- 事件: 选择 "Push"

## 📁 项目结构

```
jacocoApi/
├── main.py                          # 主 FastAPI 应用
├── github_webhook.py                # GitHub webhook 处理器
├── jacoco_tasks.py                  # Docker 扫描任务
├── config.py                        # 配置文件
├── docker/                          # Docker 相关文件
│   ├── Dockerfile.jacoco-scanner    # JaCoCo 扫描器镜像
│   └── scripts/                     # 扫描脚本
├── maven-configs/                   # Maven 配置模板
│   └── jacoco-pom-overlay.xml       # JaCoCo 配置覆盖
├── quick_start.bat                  # Windows 快速启动
├── quick_start.sh                   # Linux/Mac 快速启动
├── test_github_webhook.py           # webhook 测试脚本
├── test-docker-scan.py              # Docker 扫描测试
└── requirements.txt                 # Python 依赖
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

### 仓库配置 (`config.py`)

```python
SERVICE_CONFIG = {
    "https://github.com/your-username/your-repo.git": {
        "service_name": "your-service",
        "scan_method": "jacoco",
        "docker_image": "jacoco-scanner:latest",
        "use_docker": True,
        # ...
    }
}
```

## 🌐 API 端点

- `GET /health` - 健康检查
- `GET /docs` - API 文档
- `POST /github/webhook` - GitHub webhook 接收
- `GET /github/test` - webhook 测试端点

## 🔄 工作流程

1. **GitHub Push** → webhook 发送到 API
2. **任务排队** → Celery 将扫描任务加入队列
3. **Docker 启动** → 启动 JaCoCo 扫描容器
4. **仓库克隆** → 在容器内克隆指定提交
5. **POM 合并** → 动态合并原始 pom.xml 与 JaCoCo 配置
6. **执行扫描** → 运行 `mvn clean test jacoco:report`
7. **报告生成** → 生成 XML、HTML 和 JSON 报告
8. **结果返回** → 解析报告并返回覆盖率数据

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
```

## 📚 详细文档

- [Docker JaCoCo 使用指南](DOCKER_JACOCO_README.md)
- [GitHub Webhook 配置](GITHUB_WEBHOOK_README.md)
- [实现总结](IMPLEMENTATION_SUMMARY.md)

## 🔧 系统要求

- Python 3.8+
- Docker
- Redis (用于 Celery)
- Java 11+ (在 Docker 容器中)
- Maven 3.6+ (在 Docker 容器中)

## 🎉 当前状态

✅ 服务运行在端口 **8001**  
✅ GitHub webhook 接收正常  
✅ Docker 扫描器已配置  
✅ 无需修改原始 pom.xml  

访问 http://localhost:8001/docs 查看 API 文档！
