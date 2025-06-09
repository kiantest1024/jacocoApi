# JaCoCo Scanner API

基于FastAPI的JaCoCo代码覆盖率扫描服务，支持GitLab/GitHub webhook自动触发，多机器人配置，Web界面管理。

## ✨ 核心功能

- **Webhook集成**: 支持GitLab和GitHub webhook自动触发扫描
- **多机器人支持**: 支持配置多个Lark机器人，不同项目可使用不同机器人
- **Web管理界面**: 友好的Web界面进行配置管理
- **覆盖率报告**: 自动生成HTML和XML格式的JaCoCo报告
- **Docker支持**: 支持Docker容器化扫描和部署
- **多存储后端**: 支持文件配置和MySQL数据库存储
- **智能回退**: Docker扫描失败时自动回退到本地Maven扫描

## 📋 系统要求

- Python 3.8+
- Maven 3.6+
- Git
- MySQL 5.7+ (用于配置存储)
- Docker (可选，用于容器化扫描)

## 🚀 快速启动

### 1. 克隆项目
```bash
git clone <repository-url>
cd jacocoApi
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置MySQL数据库
确保MySQL服务运行，并创建数据库：
```sql
CREATE DATABASE jacoco_config;
```

### 4. 设置环境变量
```bash
export CONFIG_STORAGE_TYPE=mysql
export MYSQL_HOST=172.16.1.30
export MYSQL_USER=jacoco
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=jacoco_config
```

### 5. 启动服务
```bash
python start.py
```

服务将在 `http://localhost:8002` 启动。

## 📡 Webhook配置

在Git仓库设置中添加Webhook：
- **URL**: `http://your-server:8002/github/webhook-no-auth`
- **Content type**: `application/json`
- **Events**: Push events

## 🌐 Web配置界面

访问 `http://localhost:8002/config` 使用Web界面管理配置：

- 查看配置状态（机器人数量、项目映射等）
- 管理Lark机器人（添加自定义机器人）
- 配置项目映射（单个或批量添加）
- 测试机器人连接

**管理员密码**: `password`

## 📊 主要API接口

```
GET  /health              # 健康检查
GET  /config              # Web配置界面
GET  /config/status       # 获取配置状态
GET  /config/bots         # 获取机器人列表
GET  /config/mappings     # 获取项目映射
POST /config/mapping      # 添加项目映射
POST /config/bot/custom   # 添加自定义机器人
POST /github/webhook-no-auth  # Webhook接收端点
```

## 🐳 Docker部署

### 构建镜像
```bash
docker build -t jacoco-api .
```

### 运行容器
```bash
docker run -d \
  --name jacoco-api \
  -p 8002:8002 \
  -e CONFIG_STORAGE_TYPE=mysql \
  -e MYSQL_HOST=172.16.1.30 \
  -e MYSQL_USER=jacoco \
  -e MYSQL_PASSWORD=your_password \
  jacoco-api
```

### Docker Compose部署
```bash
docker-compose up -d
```

## 🐧 Linux部署

### 直接运行
```bash
# 设置环境变量
export CONFIG_STORAGE_TYPE=mysql
export MYSQL_HOST=172.16.1.30
export MYSQL_USER=jacoco
export MYSQL_PASSWORD=your_password

# 启动服务
python start.py
```

### 系统服务配置
创建systemd服务文件 `/etc/systemd/system/jacoco-api.service`：
```ini
[Unit]
Description=JaCoCo API Service
After=network.target mysql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/jacocoApi
Environment=CONFIG_STORAGE_TYPE=mysql
Environment=MYSQL_HOST=172.16.1.30
Environment=MYSQL_USER=jacoco
Environment=MYSQL_PASSWORD=your_password
ExecStart=/usr/bin/python3 start.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable jacoco-api
sudo systemctl start jacoco-api
```

## 📈 使用流程

1. **配置Webhook**: 在Git仓库中配置Webhook
2. **Web配置**: 通过Web界面配置项目和机器人映射
3. **推送代码**: 开发者推送代码触发扫描
4. **自动扫描**: 系统自动运行JaCoCo扫描
5. **发送通知**: 覆盖率结果发送到Lark机器人
6. **查看报告**: 通过链接查看详细HTML报告

## 🎯 覆盖率指标

- **指令覆盖率**: 字节码指令覆盖情况
- **分支覆盖率**: 条件分支覆盖情况
- **行覆盖率**: 源代码行覆盖情况
- **圈复杂度覆盖率**: 代码复杂度覆盖情况
- **方法覆盖率**: 方法覆盖情况
- **类覆盖率**: 类覆盖情况

## 🏗️ 项目架构

### 目录结构
```
jacocoApi/
├── app.py                    # 主应用入口
├── start.py                  # 统一启动脚本
├── src/                      # 核心源代码
│   ├── database.py           # MySQL数据库连接
│   ├── mysql_config_manager.py  # MySQL配置管理器
│   ├── docker_config_manager.py # Docker配置管理器
│   ├── jacoco_tasks.py       # JaCoCo扫描任务
│   └── lark_notification.py  # Lark通知模块
├── config/                   # 配置管理
│   └── config.py             # 文件配置管理
├── static/                   # 静态资源
│   └── templates/            # Web模板
│       └── config.html       # 配置界面
├── docker/                   # Docker相关
├── reports/                  # 报告存储目录
├── requirements.txt          # Python依赖
├── Dockerfile               # Docker镜像构建
├── docker-compose.yml       # 容器编排
└── README.md                # 项目文档
```

### 核心组件

#### 配置管理系统
- **MySQL配置管理器**: 生产环境推荐，支持动态配置
- **文件配置管理器**: 开发环境或回退方案
- **智能配置选择**: 根据环境变量自动选择配置源

#### 扫描引擎
- **Docker扫描**: 使用jacoco-scanner镜像进行隔离扫描
- **本地扫描**: 直接使用本地Maven进行扫描
- **智能回退**: Docker失败时自动切换到本地扫描

#### 通知系统
- **多机器人支持**: 不同项目可使用不同Lark机器人
- **智能通知**: 成功和失败都发送相应通知
- **丰富内容**: 包含覆盖率数据、报告链接、错误信息

## 🔧 配置说明

### 环境变量
```bash
CONFIG_STORAGE_TYPE=mysql           # 配置存储类型 (mysql/file)
MYSQL_HOST=172.16.1.30             # MySQL服务器地址
MYSQL_PORT=3306                    # MySQL端口
MYSQL_DATABASE=jacoco_config       # 数据库名
MYSQL_USER=jacoco                  # 数据库用户
MYSQL_PASSWORD=your_password       # 数据库密码
```

### 项目机器人映射
支持多种匹配方式：
- **精确匹配**: `jacocotest` -> `default`
- **通配符匹配**: `backend-*` -> `team_b`
- **URL路径匹配**: `*/team-a/*` -> `team_a`

### 机器人配置
每个机器人包含以下配置：

- **名称**: 机器人显示名称
- **Webhook URL**: Lark机器人webhook地址
- **超时时间**: 通知发送超时时间
- **重试次数**: 失败重试次数

## 🚨 故障排除

### 常见问题

#### 1. 配置页面显示undefined
- 检查MySQL连接是否正常
- 确认数据库表是否正确创建
- 验证环境变量设置

#### 2. Docker扫描失败
- 检查Docker服务状态: `docker ps`
- 确认jacoco-scanner镜像存在
- 查看Docker日志: `docker logs <container>`

#### 3. Lark通知失败
- 检查Webhook URL配置
- 确认网络连接正常
- 测试机器人连接

#### 4. Maven构建失败
- 检查pom.xml文件格式
- 确认依赖项可用
- 查看Maven输出日志

### 日志查看

```bash
# 直接运行
tail -f jacoco-api.log

# systemd服务
sudo journalctl -u jacoco-api -f

# Docker容器
docker logs -f jacoco-api
```

### 健康检查

```bash
curl http://localhost:8002/health
```

## 📊 技术栈

- **后端框架**: FastAPI
- **数据库**: MySQL 5.7+
- **容器化**: Docker + Docker Compose
- **前端**: HTML + JavaScript + Bootstrap
- **构建工具**: Maven
- **代码覆盖率**: JaCoCo
- **通知**: Lark机器人

## 🔮 扩展功能

### 已实现
- ✅ 多项目支持
- ✅ 多机器人配置
- ✅ Web管理界面
- ✅ Docker容器化
- ✅ 智能回退机制
- ✅ 错误通知处理

### 未来计划
- 支持更多Git平台（Gitee等）
- 添加更多通知渠道（钉钉、企业微信）
- 支持更多代码覆盖率工具
- 添加覆盖率趋势分析
- 支持多语言项目扫描

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目。

## 📞 支持

如有问题，请查看故障排除部分或提交Issue。
