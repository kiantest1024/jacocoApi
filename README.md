# JaCoCo API Service

一个基于 FastAPI 的 JaCoCo 代码覆盖率扫描服务，支持通过 Git webhook 自动触发扫描并发送覆盖率报告到 Lark。

## 🚀 功能特性

- 🔄 **多平台支持** - 支持 GitHub 和 GitLab webhook
- 📊 **自动扫描** - 自动生成 JaCoCo 覆盖率报告
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

### 2. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:8002` 启动。

### 3. 配置 Webhook

在 Git 仓库中配置 webhook URL：
```
http://your-server:8002/github/webhook-no-auth
```

## 📡 API 接口

### Webhook 端点
- `POST /github/webhook` - 带签名验证的 webhook
- `POST /github/webhook-no-auth` - 无签名验证（推荐）
- `GET /github/test` - 测试端点

### 健康检查
- `GET /health` - 服务状态检查

## ⚙️ 配置说明

### 核心配置 (config.py)

```python
DEFAULT_SCAN_CONFIG = {
    "scan_method": "local",           # 扫描方法
    "notification_webhook": "...",    # Lark Webhook URL
    "sync_mode": True,               # 同步模式
    "coverage_threshold": 50.0       # 覆盖率阈值
}
```

### Lark 通知配置

在 `config.py` 中设置您的 Lark 机器人 Webhook URL：
```python
"notification_webhook": "https://open.larksuite.com/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID"
```

## 🧪 测试

运行测试脚本：

```bash
# 测试完整功能
python test_webhook.py
```

### 测试内容
- ✅ 服务连接性测试
- ✅ Webhook 功能测试
- ✅ Lark 通知测试
- ✅ 覆盖率扫描测试

## 📁 项目结构

```
jacocoApi/
├── app.py                    # 🚀 主应用入口
├── config.py                 # ⚙️ 配置管理
├── jacoco_tasks.py          # 🔧 JaCoCo 扫描核心
├── github_webhook.py        # 🔗 Webhook 处理
├── feishu_notification.py   # 📱 Lark 通知
├── security.py              # 🔐 安全认证
├── requirements.txt         # 📦 依赖管理
├── test_webhook.py          # 🧪 测试脚本
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
