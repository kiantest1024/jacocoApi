# JaCoCo API Service

一个基于 FastAPI 的 JaCoCo 代码覆盖率扫描服务，支持通过 Git webhook 自动触发扫描并发送覆盖率报告到 Lark。

## 🚀 功能特性

- 🔄 **多平台支持** - 支持 GitHub 和 GitLab webhook
- � **Docker优先** - 优先使用Docker扫描，自动回退到本地扫描
- �📊 **自动扫描** - 自动生成 JaCoCo 覆盖率报告
- 🔔 **即时通知** - 支持飞书/Lark 通知推送
- 🔐 **安全认证** - 支持 webhook 签名验证
- ⚡ **同步/异步** - 支持同步和异步扫描模式
- 📈 **RESTful API** - 完整的 API 接口

## 📋 工作流程

1. **开发提交代码** → Git 仓库
2. **Git 触发 Webhook** → JaCoCo API 服务
3. **自动克隆代码** → 获取最新项目代码
4. **执行 JaCoCo 扫描** → 生成覆盖率报告
5. **推送通知** → 发送结果到 Lark 群组

## 🛠️ 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 构建Docker镜像（推荐）

```bash
# Linux/Mac
./build-docker.sh

# Windows
build-docker.bat
```

### 3. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:8002` 启动。

### 4. 配置 Webhook

在 Git 仓库中配置 webhook URL：

```text
http://your-server:8002/github/webhook-no-auth
```

## 🐳 扫描模式

### Docker扫描（推荐）
- ✅ **隔离环境** - 在独立容器中执行扫描
- ✅ **一致性** - 统一的Java和Maven环境
- ✅ **安全性** - 不影响主机环境

### 本地扫描（回退）
- ✅ **快速启动** - 无需Docker环境
- ✅ **直接执行** - 使用主机的Java和Maven
- ⚠️ **环境依赖** - 需要本地安装Java 11+和Maven 3.6+

### 自动选择策略
1. **优先Docker** - 检查Docker是否可用
2. **自动回退** - Docker不可用时使用本地扫描
3. **强制模式** - 可配置强制使用特定模式

## 📡 API 接口

### Webhook 端点
- `POST /github/webhook` - 带签名验证的 webhook
- `POST /github/webhook-no-auth` - 无签名验证（推荐）
- `GET /github/test` - 测试端点

### 报告管理
- `GET /reports` - 列出所有可用的HTML报告
- `GET /reports/{project}/{commit}/index.html` - 访问具体的HTML报告

### 健康检查
- `GET /health` - 服务状态检查

## ⚙️ 配置说明

### 环境变量配置

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

### Lark 通知配置

**环境变量方式（推荐）**：
```bash
# .env 文件
LARK_WEBHOOK_URL=https://open.larksuite.com/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID
LARK_ENABLE_NOTIFICATIONS=true
LARK_TIMEOUT=10
LARK_RETRY_COUNT=3
LARK_RETRY_DELAY=1
```

**配置项说明**：
- `LARK_WEBHOOK_URL` - Lark机器人Webhook URL（必需）
- `LARK_ENABLE_NOTIFICATIONS` - 是否启用通知（true/false）
- `LARK_TIMEOUT` - 请求超时时间（秒）
- `LARK_RETRY_COUNT` - 重试次数
- `LARK_RETRY_DELAY` - 重试延迟（秒）

### 配置管理工具

```bash
# 查看当前配置和验证
python config_manager.py

# 测试Lark连接
python config_manager.py
# 然后选择 'y' 测试连接
```

### 核心配置 (config.py)

```python
DEFAULT_SCAN_CONFIG = {
    "scan_method": "local",           # 扫描方法
    "notification_webhook": "...",    # 从环境变量读取
    "sync_mode": True,               # 同步模式
    "coverage_threshold": 50.0       # 覆盖率阈值
}
```

## 🧪 测试

运行测试脚本：

```bash
# 综合功能测试
python test_all.py
```

### 测试内容
- ✅ 服务连接性测试
- ✅ Webhook 功能测试
- ✅ Lark 通知测试
- ✅ 覆盖率扫描测试

## 📁 项目结构

```text
jacocoApi/
├── app.py                    # 🚀 主应用入口
├── config.py                 # ⚙️ 配置管理
├── jacoco_tasks.py          # 🔧 JaCoCo 扫描核心
├── github_webhook.py        # 🔗 Webhook 处理
├── feishu_notification.py   # 📱 Lark 通知
├── security.py              # 🔐 安全认证
├── requirements.txt         # 📦 依赖管理
├── config_manager.py         # 🔧 配置管理工具
├── test_all.py              # 🧪 综合测试脚本
├── .env.example             # 📝 环境变量示例
├── build-docker.sh          # 🐳 Docker构建脚本(Linux/Mac)
├── build-docker.bat         # 🐳 Docker构建脚本(Windows)
├── docker/                  # 🐳 Docker配置
│   ├── Dockerfile           # Docker镜像定义
│   └── scripts/             # 容器内脚本
│       ├── scan.sh          # 主扫描脚本
│       ├── enhance-pom.sh   # pom.xml增强脚本
│       └── generate-summary.sh # 摘要生成脚本
├── reports/                 # 📊 生成的HTML报告文件
└── README.md               # 📖 项目文档
```

## 📊 覆盖率报告

系统会自动生成并发送包含以下JaCoCo标准覆盖率指标的报告：

### 🎯 **覆盖率指标（6项）**
- ⚡ **指令覆盖率** - 字节码指令覆盖百分比
- 🌿 **分支覆盖率** - 条件分支覆盖百分比
- 🎯 **行覆盖率** - 源代码行覆盖百分比
- 🔄 **圈复杂度覆盖率** - 代码复杂度覆盖百分比
- 🔧 **方法覆盖率** - 方法覆盖百分比
- 📦 **类覆盖率** - 类覆盖百分比

### 📋 **报告信息**
- 📋 **项目信息** - 仓库、分支、提交信息
- ⏰ **扫描时间** - 扫描完成时间
- 📊 **详细统计** - 覆盖/总计数量
- 🔗 **HTML报告链接** - 点击查看详细的可视化报告

### 🌐 **HTML报告功能**

系统会自动生成并托管HTML格式的JaCoCo报告：

- **📊 自动生成** - 每次扫描自动生成HTML报告
- **🔗 Lark链接** - 通知消息中包含"查看详细报告"按钮
- **📱 一键访问** - 点击按钮直接在浏览器中查看报告
- **📂 报告管理** - 按项目和提交ID组织存储
- **🌍 Web访问** - 通过 `/reports` API查看所有报告

**访问方式**：
- 通过Lark通知中的按钮直接访问
- 访问 `http://localhost:8002/reports` 查看所有报告
- 直接访问 `http://localhost:8002/reports/{项目名}/{提交ID}/index.html`

## 🔧 故障排除

### 常见问题

**1. 扫描失败**
- ✅ 确认项目为 Maven 项目（有 pom.xml）
- ✅ 检查 Java 和 Maven 环境
- ✅ 查看服务端详细日志

**2. 通知未发送**
- ✅ 检查 Lark webhook URL 配置
- ✅ 确认网络连接正常
- ✅ 查看通知相关日志

**3. Webhook 无响应**
- ✅ 确认服务正在运行
- ✅ 检查端口是否被占用
- ✅ 验证 webhook URL 配置

### 日志分析

服务运行时输出详细日志：
```
[req_xxx] 使用同步模式执行扫描
[req_xxx] ==================== 通知调试开始 ====================
[req_xxx] ✅ 飞书通知发送成功
```

## 📄 许可证

MIT License
