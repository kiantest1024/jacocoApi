# Universal JaCoCo Scanner API

通用JaCoCo代码覆盖率扫描服务，支持GitHub和GitLab webhook触发。

## 🚀 主要特性

- 支持任何Maven项目，无需修改项目配置
- 同时支持GitHub和GitLab webhook
- 自动生成HTML/XML覆盖率报告
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

### 4. 测试功能
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

### 全局Lark通知配置
在 `config.py` 中统一配置Lark机器人：

```python
LARK_CONFIG = {
    "webhook_url": "https://open.larksuite.com/open-apis/bot/v2/hook/your-webhook-id",
    "enable_notifications": True,
    "timeout": 10,
    "retry_count": 3,
    "retry_delay": 1,
}
```

所有项目将使用此全局配置发送通知，确保通知的一致性。

## 🔧 项目结构

```
jacocoApi/
├── app.py              # 主应用文件
├── config.py           # 配置管理
├── jacoco_tasks.py     # 扫描任务处理
├── lark_notification.py    # Lark通知发送
├── test_simple.py      # 简单测试脚本
├── requirements.txt    # Python依赖
└── README.md          # 项目文档
```

## 📊 覆盖率报告

支持XML和HTML格式报告，包含指令、分支、行、方法、类和复杂度覆盖率。

## 🔔 通知配置

扫描完成后自动发送Lark通知，包含项目信息、覆盖率数据和HTML报告链接。

## 📄 许可证

MIT License
