# JaCoCo Scanner API

JaCoCo代码覆盖率扫描服务，支持GitHub和GitLab webhook触发。

## 🚀 主要特性

- 支持Maven项目自动扫描
- 支持GitHub和GitLab webhook
- Docker扫描优先，本地扫描回退
- 自动生成HTML/XML报告
- 自动发送Lark通知

## 📋 工作流程

1. 开发提交代码 → Git仓库
2. Git触发Webhook → JaCoCo API服务
3. 自动克隆代码 → 获取最新项目代码
4. 执行JaCoCo扫描 → 生成覆盖率报告
5. 推送通知 → 发送结果到Lark群组

## 🛠️ 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务
```bash
python app.py
```

### 3. 配置webhook
在GitHub或GitLab项目中配置webhook：
- URL: `http://your-server:8002/github/webhook-no-auth`
- Content type: `application/json`
- Events: Push events

### 4. Docker部署（推荐）

#### 方式1: 快速部署
```bash
chmod +x quick-deploy.sh
./quick-deploy.sh
```

#### 方式2: Docker Compose部署
```bash
chmod +x deploy.sh
./deploy.sh
```

#### 方式3: 手动Docker部署
```bash
# 构建镜像
docker build -f Dockerfile.service -t jacoco-scanner-api .

# 运行容器
docker run -d \
  --name jacoco-scanner-api \
  -p 8002:8002 \
  -v $(pwd)/reports:/app/reports \
  jacoco-scanner-api
```

### 5. 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py

# 测试功能
python test_simple.py
```

## 📋 API接口

### 核心接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 服务根路径，返回基本信息 |
| `/health` | GET | 健康检查接口 |
| `/github/webhook-no-auth` | POST | GitHub/GitLab webhook接口（无认证） |
| `/reports` | GET | 列出所有可用的覆盖率报告 |
| `/reports/{service}/{commit}/index.html` | GET | 访问特定的HTML覆盖率报告 |

## ⚙️ 配置说明

在 `config.py` 中配置Lark通知URL。

## 🔧 项目结构

```
jacocoApi/
├── app.py              # 主应用
├── config.py           # 配置管理
├── jacoco_tasks.py     # 扫描任务
├── lark_notification.py # Lark通知
├── test_simple.py      # 测试脚本
├── Dockerfile          # Docker扫描镜像
├── Dockerfile.service  # API服务镜像
├── docker-compose.yml  # Docker Compose配置
├── deploy.sh           # 完整部署脚本
├── quick-deploy.sh     # 快速部署脚本
├── docker_scan.sh      # Docker扫描脚本
├── entrypoint.sh       # Docker入口点
├── build_docker.sh     # 扫描镜像构建
├── requirements.txt    # Python依赖
├── .dockerignore       # Docker忽略文件
└── README.md          # 项目文档
```

## � Docker部署说明

### 部署方式对比

| 方式 | 命令 | 特点 |
|------|------|------|
| 快速部署 | `./quick-deploy.sh` | 一键部署，适合快速测试 |
| Compose部署 | `./deploy.sh` | 完整配置，适合生产环境 |
| 手动部署 | `docker build && docker run` | 自定义配置 |

### 服务访问

部署成功后可访问：
- API服务: http://localhost:8002
- API文档: http://localhost:8002/docs
- 健康检查: http://localhost:8002/health
- 报告列表: http://localhost:8002/reports

### 管理命令

```bash
# 查看服务状态
docker ps | grep jacoco

# 查看服务日志
docker logs jacoco-scanner-api

# 停止服务
docker stop jacoco-scanner-api

# 重启服务
docker restart jacoco-scanner-api
```

### 故障排除

如果遇到部署问题：

1. **Java包安装失败**: 脚本会自动尝试Ubuntu基础镜像
2. **端口占用**: 检查并停止现有容器
3. **权限问题**: 确保用户在docker组中
4. **详细指南**: 查看 [DOCKER_TROUBLESHOOTING.md](DOCKER_TROUBLESHOOTING.md)

## �📊 覆盖率报告

支持XML和HTML格式报告，包含指令、分支、行、方法、类和复杂度覆盖率。

## 📄 许可证

MIT License
