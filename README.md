# Universal JaCoCo Scanner API

通用JaCoCo代码覆盖率扫描服务，支持GitHub和GitLab webhook触发，为任何Maven项目提供自动化代码覆盖率分析。

## 🚀 主要特性

- **通用性**: 支持任何Maven项目，无需修改项目配置
- **多平台支持**: 同时支持GitHub和GitLab webhook
- **自动化**: webhook触发自动扫描，无需手动操作
- **实时通知**: 扫描完成后自动发送Lark通知
- **报告管理**: 自动生成和管理HTML/XML覆盖率报告

## 📋 工作流程

1. **开发提交代码** → Git 仓库
2. **Git 触发 Webhook** → JaCoCo API 服务
3. **自动克隆代码** → 获取最新项目代码
4. **执行 JaCoCo 扫描** → 生成覆盖率报告
5. **推送通知** → 发送结果到 Lark 群组

## 🛠️ 快速开始

### 1. 环境要求

- Python 3.8+
- Maven 3.6+
- Git

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:8002` 启动

### 4. 配置webhook

在你的GitHub或GitLab项目中配置webhook：

- **URL**: `http://your-server:8002/github/webhook-no-auth`
- **Content type**: `application/json`
- **Events**: Push events

### 5. 测试功能

```bash
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

### 基本配置 (config.py)

```python
DEFAULT_SCAN_CONFIG = {
    "scan_method": "jacoco",
    "project_type": "maven",
    "use_docker": False,  # 使用本地扫描
    "force_local_scan": True,  # 强制本地扫描
    "sync_mode": True,  # 同步模式
    "scan_timeout": 1800,  # 扫描超时时间(秒)
    "notification_webhook": "your-lark-webhook-url"
}
```

## 🔧 项目结构

```
jacocoApi/
├── app.py              # 主应用文件
├── config.py           # 配置管理
├── jacoco_tasks.py     # 扫描任务处理
├── feishu_notification.py  # 通知发送
├── test_simple.py      # 简单测试脚本
├── requirements.txt    # Python依赖
└── README.md          # 项目文档
```

## 📊 覆盖率报告

### 支持的报告格式

- **XML**: 机器可读格式，用于数据分析
- **HTML**: 人类可读格式，用于浏览器查看

### 报告访问

- **列出所有报告**: `GET /reports`
- **访问HTML报告**: `GET /reports/{service}/{commit}/index.html`

### 覆盖率指标

- **指令覆盖率** (Instruction Coverage)
- **分支覆盖率** (Branch Coverage)
- **行覆盖率** (Line Coverage)
- **方法覆盖率** (Method Coverage)
- **类覆盖率** (Class Coverage)
- **复杂度覆盖率** (Complexity Coverage)

## 🔔 通知配置

### Lark通知

扫描完成后会自动发送Lark通知，包含：

- 项目信息
- 覆盖率数据
- HTML报告链接
- 扫描状态

配置Lark webhook URL：

```python
"notification_webhook": "https://open.larksuite.com/open-apis/bot/v2/hook/your-webhook-id"
```

## 🐛 故障排除

### 常见问题

1. **覆盖率为0%**
   - 检查项目是否有测试代码
   - 验证JaCoCo插件配置
   - 确认测试正常执行

2. **扫描超时**
   - 增加 `scan_timeout` 配置
   - 检查网络连接
   - 优化Maven依赖

3. **服务无响应**
   - 检查端口占用
   - 查看服务日志
   - 重启服务

## 📝 更新日志

### v2.0.0
- 简化项目结构，移除冗余代码
- 优化配置管理
- 改进错误处理
- 增强日志输出
- 更新文档

## 📄 许可证

MIT License
