# JaCoCo Scanner API

基于FastAPI的JaCoCo代码覆盖率扫描服务，支持通过Webhook自动触发Java项目的代码覆盖率分析，并将结果发送到Lark机器人。

## 🚀 主要功能

- **Webhook支持**: 支持GitHub和GitLab的Push事件
- **自动扫描**: 自动克隆代码、运行测试、生成JaCoCo报告
- **多环境支持**: 支持Docker容器扫描和本地Maven扫描
- **智能通知**: 自动发送覆盖率报告到Lark机器人
- **多机器人配置**: 支持为不同项目配置不同的Lark机器人
- **Web配置界面**: 提供友好的Web界面管理配置
- **MySQL存储**: 配置数据持久化存储到MySQL数据库

## 📋 系统要求

- Python 3.8+
- Maven 3.6+
- Git
- MySQL 5.7+ (用于配置存储)
- Docker (可选，用于容器化扫描)

## 🛠️ 快速启动

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

### 4. 启动服务
```bash
python start.py
```

服务将在 `http://localhost:8002` 启动。

## 📡 Webhook配置

在Git仓库设置中添加Webhook：
- **URL**: `http://your-server:8002/github/webhook-no-auth`
- **Content type**: `application/json`
- **Events**: Push events

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

## 🌐 Web配置界面

访问 `http://localhost:8002/config` 使用Web界面管理配置：

- 查看配置状态（机器人数量、项目映射等）
- 管理Lark机器人（添加自定义机器人）
- 配置项目映射（单个或批量添加）
- 测试机器人连接

## 🔧 配置说明

### 环境变量
```bash
CONFIG_STORAGE_TYPE=mysql           # 配置存储类型
MYSQL_HOST=172.16.1.30             # MySQL服务器地址
MYSQL_PORT=3306                    # MySQL端口
MYSQL_DATABASE=jacoco_config       # 数据库名
MYSQL_USER=jacoco                  # 数据库用户
MYSQL_PASSWORD=your_password       # 数据库密码
```

### 管理员密码
Web界面管理员操作密码：`password`

## 🐳 Docker部署

### 构建镜像
```bash
docker build -t jacoco-api .
```

### 运行容器
```bash
docker run -d \
  -p 8002:8002 \
  -e CONFIG_STORAGE_TYPE=mysql \
  -e MYSQL_HOST=your_mysql_host \
  -e MYSQL_PASSWORD=your_password \
  jacoco-api
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

## 🚨 故障排除

### 常见问题

1. **配置页面显示undefined**
   - 检查MySQL连接是否正常
   - 确认数据库表是否正确创建

2. **Docker扫描失败**
   - 检查Docker服务状态
   - 确认jacoco-scanner镜像存在

3. **Lark通知失败**
   - 检查Webhook URL配置
   - 确认网络连接正常

### 日志查看
应用日志会输出到控制台，包含详细的扫描和通知信息。

## 📁 项目结构

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
└── README.md                # 项目文档
```

## 📄 许可证

MIT License
