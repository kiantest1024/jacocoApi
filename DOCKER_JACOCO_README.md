# Docker JaCoCo 覆盖率扫描系统

这是一个基于 Docker 容器的 JaCoCo 覆盖率扫描系统，可以在不修改原始 Java 项目 pom.xml 的情况下，通过 GitHub webhook 触发自动化的覆盖率统计。

## 系统架构

```
GitHub Webhook → FastAPI → Celery → Docker Container → JaCoCo Reports
```

### 核心特性

- ✅ **无侵入性**: 不需要修改原始项目的 pom.xml 文件
- ✅ **Docker 隔离**: 在独立的 Docker 容器中执行扫描
- ✅ **外部配置**: 使用外部 Maven 配置文件添加 JaCoCo 插件
- ✅ **自动化**: 通过 GitHub webhook 自动触发
- ✅ **多格式报告**: 生成 XML、HTML 和 JSON 格式的报告

## 文件结构

```
jacocoApi/
├── docker/
│   ├── Dockerfile.jacoco-scanner     # Docker 镜像定义
│   └── scripts/
│       ├── scan.sh                   # 主扫描脚本
│       ├── generate-enhanced-pom.sh  # POM 文件生成脚本
│       └── generate-summary.sh       # 报告摘要生成脚本
├── maven-configs/
│   └── jacoco-pom-overlay.xml        # JaCoCo Maven 配置模板
├── github_webhook.py                 # GitHub webhook 处理器
├── jacoco_tasks.py                   # Docker 扫描任务 (已更新)
├── config.py                         # 配置文件 (已更新)
├── build-docker.sh                   # Docker 构建脚本
├── test-docker-scan.py               # Docker 扫描测试脚本
└── DOCKER_JACOCO_README.md           # 本文档
```

## 快速开始

### 1. 构建 Docker 镜像

```bash
cd Script/GE/jacocoApi

# 使用构建脚本
./build-docker.sh

# 或手动构建
docker build -t jacoco-scanner:latest -f docker/Dockerfile.jacoco-scanner .
```

### 2. 测试 Docker 扫描

```bash
# 测试 Docker 扫描功能
python test-docker-scan.py
```

### 3. 启动 API 服务

```bash
# 启动完整服务
python start_github_webhook.py

# 或使用快速启动脚本
./quick_start.sh  # Linux/Mac
quick_start.bat   # Windows
```

### 4. 配置 GitHub Webhook

在您的 GitHub 仓库中设置 webhook：
- URL: `http://your-server:8000/github/webhook`
- Content type: `application/json`
- Secret: 在 `.env` 文件中配置的密钥
- 事件: 选择 "Push" 事件

## 工作流程

### 1. GitHub Webhook 触发
当您向 GitHub 推送代码时，GitHub 发送 webhook 到您的 API。

### 2. 任务排队
API 接收 webhook，验证签名，并将扫描任务添加到 Celery 队列。

### 3. Docker 容器执行
Celery worker 启动 Docker 容器执行以下步骤：

1. **克隆仓库**: 在容器内克隆指定的 Git 仓库和提交
2. **生成增强 POM**: 将原始 pom.xml 与 JaCoCo 配置模板合并
3. **运行测试**: 执行 `mvn clean test jacoco:report`
4. **生成报告**: 创建 XML、HTML 和 JSON 格式的报告
5. **输出结果**: 将报告文件复制到主机目录

### 4. 报告解析
API 解析生成的报告文件，提取覆盖率数据。

### 5. 结果返回
将覆盖率统计结果返回给调用方，并可选发送通知。

## Docker 容器详情

### 基础镜像
- `maven:3.9.4-openjdk-11-slim`

### 安装的工具
- Git (用于克隆仓库)
- xmlstarlet (用于 XML 处理)
- bc (用于数学计算)
- 其他必要的 Linux 工具

### 目录结构
```
/app/
├── workspace/          # 工作目录
├── configs/           # Maven 配置文件
├── reports/           # 报告输出目录
└── scripts/           # 扫描脚本
```

## Maven 配置覆盖

### 外部配置文件
`maven-configs/jacoco-pom-overlay.xml` 包含：
- JaCoCo Maven 插件配置
- Surefire 插件配置
- 覆盖率检查规则
- 报告生成配置

### POM 合并过程
1. 解析原始 pom.xml 提取项目信息
2. 从模板复制 JaCoCo 配置
3. 合并依赖项和属性
4. 生成增强的 pom.xml

## 报告格式

### XML 报告 (`jacoco.xml`)
标准的 JaCoCo XML 格式，包含详细的覆盖率数据。

### HTML 报告 (`html/`)
可视化的 HTML 报告，包含：
- 总体覆盖率统计
- 包级别覆盖率
- 类级别覆盖率
- 源代码覆盖率高亮

### JSON 摘要 (`summary.json`)
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "coverage": {
    "line": {
      "percentage": 75.5,
      "covered": 151,
      "total": 200
    },
    "branch": {
      "percentage": 68.2,
      "covered": 30,
      "total": 44
    }
  },
  "summary": {
    "overall_coverage": 75.5,
    "status": "good"
  }
}
```

## 配置选项

### 服务配置 (`config.py`)
```python
SERVICE_CONFIG = {
    "https://github.com/your-username/your-repo.git": {
        "service_name": "your-service",
        "scan_method": "jacoco",
        "project_type": "maven",
        "docker_image": "jacoco-scanner:latest",
        "coverage_threshold": 50.0,
        "use_docker": True,
        # ...
    }
}
```

### 环境变量 (`.env`)
```env
# Docker 配置
DOCKER_IMAGE=jacoco-scanner:latest
DOCKER_TIMEOUT=1800

# JaCoCo 配置
JACOCO_VERSION=0.8.10
COVERAGE_THRESHOLD=50.0

# GitHub Webhook
GIT_WEBHOOK_SECRET=your_secret_here
```

## 测试和调试

### 本地测试
```bash
# 测试 Docker 镜像构建
./build-docker.sh

# 测试扫描功能
python test-docker-scan.py

# 手动运行 Docker 扫描
docker run --rm \
  -v $(pwd)/reports:/app/reports \
  jacoco-scanner:latest \
  --repo-url https://github.com/user/repo.git \
  --commit-id abc123 \
  --branch main
```

### 调试模式
设置环境变量 `DEBUG=True` 启用详细日志。

### 查看容器日志
```bash
# 查看运行中的容器
docker ps

# 查看容器日志
docker logs <container_id>
```

## 故障排除

### 常见问题

1. **Docker 镜像构建失败**
   - 检查 Dockerfile 路径
   - 确保所有必需文件存在
   - 检查网络连接

2. **扫描超时**
   - 增加 Docker 超时时间
   - 检查项目大小和复杂度
   - 优化 Maven 配置

3. **报告生成失败**
   - 检查 Maven 测试是否通过
   - 验证 JaCoCo 配置
   - 查看容器内的错误日志

4. **权限问题**
   - 确保 Docker 有足够权限
   - 检查文件系统权限
   - 使用非 root 用户运行

### 日志查看
- API 日志: `logs/jacoco_api.log`
- Celery 日志: `logs/celery.log`
- Docker 输出: 在任务结果中

## 性能优化

### Docker 镜像优化
- 使用多阶段构建
- 预下载 Maven 依赖
- 优化镜像层

### 扫描优化
- 并行测试执行
- 增量构建
- 缓存 Maven 仓库

## 安全考虑

- Docker 容器以非 root 用户运行
- 网络隔离
- 临时文件自动清理
- 敏感信息不写入日志

## 扩展功能

### 支持其他构建工具
- Gradle 支持
- SBT 支持
- Ant 支持

### 多语言支持
- 添加其他语言的覆盖率工具
- 统一报告格式

这个 Docker 化的解决方案提供了一个完全隔离、可扩展的 JaCoCo 覆盖率扫描系统，无需修改原始项目代码。
