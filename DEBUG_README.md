# JaCoCo API 调试版本使用指南

## 🔍 调试版本特性

调试版本提供了详细的扫描日志和构建信息输出，帮助开发者深入了解 JaCoCo 扫描过程。

### ✨ 主要功能

- **详细日志输出**: 记录每个构建步骤的详细信息
- **Maven 命令跟踪**: 显示所有 Maven 命令的执行过程和输出
- **项目结构分析**: 检查源代码和测试代码的结构
- **构建过程监控**: 实时显示编译、测试、报告生成过程
- **错误诊断**: 详细的错误信息和堆栈跟踪
- **性能监控**: 记录每个步骤的执行时间

### 🆚 与正常版本的区别

| 功能 | 正常版本 | 调试版本 |
|------|----------|----------|
| 端口 | 8002 | 8003 |
| 日志级别 | INFO | DEBUG |
| 日志文件 | 无 | jacoco_debug.log |
| Maven 输出 | 简化 | 完整显示 |
| 错误信息 | 基本 | 详细堆栈 |
| 性能监控 | 无 | 有 |
| 调试接口 | 无 | /debug/logs |

## 🚀 快速启动

### Linux/macOS

```bash
# 给启动脚本执行权限
chmod +x start_debug.sh

# 启动调试服务
./start_debug.sh
```

### Windows

```cmd
# 直接运行批处理文件
start_debug.bat
```

### 手动启动

```bash
# 设置环境变量
export CONFIG_STORAGE_TYPE=file
export JACOCO_DEBUG_MODE=true
export JACOCO_VERBOSE_LOGGING=true

# 启动调试应用
python app_debug.py
```

## 📡 调试接口

### 基本接口

- **服务地址**: http://localhost:8003
- **API 文档**: http://localhost:8003/docs
- **健康检查**: http://localhost:8003/health

### 调试专用接口

#### GET /debug/logs
获取最近的调试日志

```bash
curl http://localhost:8003/debug/logs
```

响应示例：
```json
{
  "status": "success",
  "logs": ["2025-06-20 17:00:00 - DEBUG - ...", "..."],
  "total_lines": 1500,
  "message": "最近100行调试日志"
}
```

#### POST /github/webhook-no-auth
调试版本的 Webhook 处理器，提供详细的扫描日志

## 📋 调试日志说明

### 日志级别

- **DEBUG**: 详细的调试信息，包括变量值、函数调用等
- **INFO**: 一般信息，包括步骤进度、状态更新
- **WARNING**: 警告信息，包括非致命错误、回退操作
- **ERROR**: 错误信息，包括异常和失败操作

### 日志格式

```
2025-06-20 17:00:00,123 - module_name - LEVEL - [filename:line] - [request_id] message
```

### 关键日志标识

- `[DEBUG]`: 调试信息
- `[request_id]`: 请求标识符
- `🔧`: 命令执行
- `📤`: 标准输出
- `📥`: 标准错误
- `⏱️`: 执行时间
- `📊`: 分析结果

## 🔍 调试场景示例

### 1. Maven 构建过程调试

调试版本会详细记录每个 Maven 目标的执行：

```
[req_123] 🔨 [Maven clean (1/3)] 开始执行Maven命令...
[req_123] [DEBUG] 工作目录: /tmp/jacoco_local_req_123_abc
[req_123] [DEBUG] 命令: mvn clean -B -e
[req_123] [DEBUG] 超时时间: 600秒
[req_123] 🔧 [Maven clean (1/3)] 执行命令: mvn clean -B -e
[req_123] STDOUT: [INFO] Scanning for projects...
[req_123] STDOUT: [INFO] Building test-project 1.0.0
[req_123] ⏱️  [Maven clean (1/3)] 执行时间: 2.34秒
[req_123] ✅ [Maven clean (1/3)] 执行成功
```

### 2. 测试执行分析

```
[req_123] 📊 Maven输出分析结果:
[req_123]   测试运行: 15
[req_123]   测试失败: 2
[req_123]   测试错误: 0
[req_123]   测试跳过: 1
[req_123]   编译错误: 0
[req_123]   构建警告: 3
```

### 3. 项目结构检查

```
[req_123] 📁 项目结构检查:
[req_123]   主代码目录: ✅ /tmp/project/src/main/java
[req_123]   测试代码目录: ✅ /tmp/project/src/test/java
[req_123]   主代码文件数: 25
[req_123]   测试代码文件数: 18
```

## 🛠️ 故障排除

### 常见问题

#### 1. 端口冲突
```
⚠️  端口8003已被占用
```

**解决方案**：
- 关闭占用端口的程序
- 或修改 `app_debug.py` 中的端口号

#### 2. 依赖缺失
```
❌ ModuleNotFoundError: No module named 'xxx'
```

**解决方案**：
```bash
pip install -r requirements.txt
```

#### 3. 权限问题
```
❌ Permission denied
```

**解决方案**：
```bash
chmod +x start_debug.sh
```

### 调试技巧

#### 1. 实时查看日志
```bash
tail -f jacoco_debug.log
```

#### 2. 过滤特定请求的日志
```bash
grep "req_123" jacoco_debug.log
```

#### 3. 查看错误日志
```bash
grep "ERROR\|❌" jacoco_debug.log
```

#### 4. 分析 Maven 输出
```bash
grep "STDOUT\|STDERR" jacoco_debug.log
```

## 📈 性能分析

调试版本会记录各个步骤的执行时间：

```
[req_123] ⏱️  [仓库克隆] 执行时间: 5.23秒
[req_123] ⏱️  [Maven clean] 执行时间: 2.34秒
[req_123] ⏱️  [Maven test] 执行时间: 45.67秒
[req_123] ⏱️  [Maven jacoco:report] 执行时间: 8.91秒
```

## 🔒 安全注意事项

- 调试版本会记录详细信息，包括可能的敏感数据
- 生产环境请使用正常版本
- 定期清理调试日志文件
- 不要在公网暴露调试端口

## 📞 技术支持

如果在使用调试版本时遇到问题：

1. 查看 `jacoco_debug.log` 文件
2. 访问 `/debug/logs` 接口获取最新日志
3. 检查 Maven 和 Docker 环境
4. 确认项目结构和依赖配置

## 🔄 版本切换

### 切换到调试版本
```bash
./start_debug.sh    # Linux/macOS
start_debug.bat     # Windows
```

### 切换回正常版本
```bash
python app.py       # 端口 8002
```
