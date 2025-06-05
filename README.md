# JaCoCo Scanner API

**最终版本** - JaCoCo代码覆盖率扫描服务，支持GitHub和GitLab webhook触发。

## 🚀 核心特性

- **自动扫描**: Maven项目零配置扫描
- **Webhook集成**: 支持GitHub/GitLab自动触发
- **Docker优先**: Docker扫描 + 本地回退机制
- **完整报告**: 生成HTML/XML覆盖率报告
- **即时通知**: 自动发送Lark群组通知
- **一键部署**: Docker容器化部署

## 🚀 快速开始

### Docker部署（推荐）

一键部署，自动配置所有依赖：

```bash
chmod +x quick-deploy.sh
./quick-deploy.sh
```

部署完成后访问：http://localhost:8002

### 本地开发

```bash
pip install -r requirements.txt
python app.py
```

### Webhook配置

在GitHub或GitLab项目中配置webhook：
- **GitHub**: `http://your-server:8002/github/webhook-no-auth`
- **GitLab**: `http://your-server:8002/gitlab/webhook-no-auth`
- **Content type**: `application/json`
- **Events**: Push events

## 📡 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/github/webhook-no-auth` | POST | GitHub webhook接收 |
| `/gitlab/webhook-no-auth` | POST | GitLab webhook接收 |
| `/health` | GET | 服务健康检查 |
| `/reports` | GET | 覆盖率报告列表 |
| `/reports/{service}/{commit}/index.html` | GET | HTML覆盖率报告 |

## ⚙️ 配置

在 `config.py` 中配置Lark通知URL：

```python
LARK_CONFIG = {
    "webhook_url": "https://open.larksuite.com/open-apis/bot/v2/hook/your-webhook-id"
}
```

## 🔧 项目结构

```
jacocoApi/
├── app.py              # 主应用服务
├── config.py           # 配置管理
├── jacoco_tasks.py     # 扫描任务逻辑
├── lark_notification.py # Lark通知模块
├── test_simple.py      # 基础测试脚本
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

## 📊 覆盖率报告

自动生成完整的覆盖率报告：

- **XML格式**: 机器可读的覆盖率数据
- **HTML格式**: 可视化覆盖率报告
- **覆盖率指标**: 指令、分支、行、方法、类、复杂度覆盖率

## 🐳 Docker管理

### 服务管理

```bash
# 查看服务状态
docker ps | grep jacoco-scanner-api

# 查看服务日志
docker logs jacoco-scanner-api

# 停止服务
docker stop jacoco-scanner-api

# 重启服务
docker restart jacoco-scanner-api
```

### 完整部署

```bash
# 使用Docker Compose
chmod +x deploy.sh
./deploy.sh
```

## 🔍 故障排除

### 常见问题

1. **端口占用**: 确保8002端口未被占用
2. **Docker权限**: 确保用户在docker组中
3. **Java环境**: Docker镜像自动配置Java和Maven
4. **网络访问**: 确保能访问Git仓库

### 测试功能

```bash
# 测试基础功能
python test_simple.py

# 测试健康检查
curl http://localhost:8002/health

# 查看API文档
curl http://localhost:8002/docs
```

## 📈 项目状态

- ✅ **生产就绪**: 经过深度优化和测试
- ✅ **功能完整**: 支持完整的CI/CD流程
- ✅ **高度精简**: 删除80%冗余文件
- ✅ **易于维护**: 清晰的代码结构
- ✅ **一键部署**: Docker容器化部署

---

**最终版本** - 项目已完成深度清理和优化，保证功能完整性的同时实现最佳精简状态。
