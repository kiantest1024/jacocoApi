# Linux 环境设置指南

解决 Python 3.12+ 环境中的 `distutils` 模块缺失问题。

## 问题描述

在 Python 3.12+ 中，`distutils` 模块已被移除，但某些依赖库（如 `dockerpycreds`）仍在使用它，导致以下错误：

```
ModuleNotFoundError: No module named 'distutils'
```

## 解决方案

### 方案 1: 使用修复版本的依赖（推荐）

1. **使用专门的 Linux requirements 文件**:
   ```bash
   pip install -r requirements-linux.txt
   ```

2. **使用 Linux 专用启动脚本**:
   ```bash
   chmod +x start_linux.sh
   ./start_linux.sh
   ```

### 方案 2: 手动修复步骤

1. **安装 setuptools**（替代 distutils）:
   ```bash
   pip install setuptools>=68.0.0
   ```

2. **避免使用有问题的 docker 库**:
   ```bash
   # 不安装 docker 库，改用 subprocess 调用
   pip install fastapi uvicorn celery redis requests python-dotenv pydantic
   ```

3. **启动服务**:
   ```bash
   python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
   ```

### 方案 3: 使用 Python 3.11

如果可能，建议使用 Python 3.11 而不是 3.12+：

```bash
# 使用 pyenv 安装 Python 3.11
pyenv install 3.11.6
pyenv local 3.11.6

# 或使用系统包管理器
sudo apt install python3.11 python3.11-venv
```

## 测试修复

运行测试脚本验证修复：

```bash
python3 test_celery_import.py
```

## 功能限制

在避免使用 docker 库的情况下：

- ✅ **GitHub Webhook 接收**: 完全可用
- ✅ **Ping 事件处理**: 完全可用  
- ✅ **Push 事件处理**: 可用（需要 Redis）
- ⚠️ **JaCoCo 扫描**: 使用 subprocess 调用 docker 命令

## 启动服务

### 完整启动（推荐）

```bash
# 1. 启动 Redis
docker run -d -p 6379:6379 redis:alpine

# 2. 使用 Linux 启动脚本
./start_linux.sh
```

### 最小启动（仅 API）

```bash
# 仅启动 API 服务（不包含 Celery）
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### 分步启动

```bash
# 1. 启动 Celery worker
celery -A jacoco_tasks.celery_app worker --loglevel=info

# 2. 启动 FastAPI 服务器
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
```

## 验证服务

```bash
# 健康检查
curl http://localhost:8001/health

# GitHub webhook 测试
curl http://localhost:8001/github/test

# API 文档
# 浏览器访问: http://localhost:8001/docs
```

## 故障排除

### 1. Celery 启动失败

**错误**: `Unable to load celery application`

**解决**:
```bash
# 确保在正确的目录中
cd /path/to/jacocoApi

# 检查 Python 路径
export PYTHONPATH=$PWD:$PYTHONPATH

# 重新启动
celery -A jacoco_tasks.celery_app worker --loglevel=info
```

### 2. Redis 连接失败

**错误**: Redis 连接被拒绝

**解决**:
```bash
# 启动 Redis
docker run -d -p 6379:6379 redis:alpine

# 或使用系统服务
sudo systemctl start redis
```

### 3. Docker 权限问题

**错误**: Docker 权限被拒绝

**解决**:
```bash
# 将用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或重启会话
newgrp docker
```

## 环境变量

在 `.env` 文件中配置：

```env
# GitHub Webhook
GIT_WEBHOOK_SECRET=your_secret_here

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# 调试
DEBUG=True
LOG_LEVEL=INFO
```

## 生产环境建议

1. **使用 systemd 服务**:
   ```bash
   sudo systemctl enable jacoco-api
   sudo systemctl start jacoco-api
   ```

2. **使用 nginx 反向代理**:
   ```nginx
   location /github/webhook {
       proxy_pass http://localhost:8001;
   }
   ```

3. **使用 Docker Compose**:
   ```yaml
   version: '3.8'
   services:
     api:
       build: .
       ports:
         - "8001:8001"
     redis:
       image: redis:alpine
       ports:
         - "6379:6379"
   ```

这样就可以在 Linux 环境中成功运行服务了！
