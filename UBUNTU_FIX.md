# Ubuntu Linux 启动修复指南

## 问题已修复 ✅

我们已经修复了以下问题：
1. ✅ Python 3.12+ `distutils` 模块缺失
2. ✅ `ModuleNotFoundError: No module named 'tasks'`
3. ✅ Docker 库兼容性问题

## 在 Ubuntu 服务器上启动服务

### 方法 1: 使用修复后的启动脚本（推荐）

```bash
# 1. 进入项目目录
cd /home/automated/project/jacocoApi

# 2. 设置脚本权限
chmod +x start_linux.sh

# 3. 启动服务
./start_linux.sh
```

### 方法 2: 手动步骤

```bash
# 1. 进入项目目录
cd /home/automated/project/jacocoApi

# 2. 创建虚拟环境（如果没有）
python3 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 升级 pip 和安装 setuptools
pip install --upgrade pip
pip install setuptools>=68.0.0

# 5. 安装依赖
pip install -r requirements-linux.txt

# 6. 创建环境配置文件（如果没有）
cp .env.example .env

# 7. 启动 Redis（可选，用于 Celery）
docker run -d -p 6379:6379 redis:alpine

# 8. 启动 Celery worker（如果有 Redis）
celery -A jacoco_tasks.celery_app worker --loglevel=info --detach

# 9. 启动 FastAPI 服务器
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### 方法 3: 最小启动（仅 API，无 Celery）

```bash
# 如果不需要 Celery 功能，可以只启动 API
cd /home/automated/project/jacocoApi
source venv/bin/activate
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
```

## 验证服务启动

```bash
# 健康检查
curl http://localhost:8001/health

# GitHub webhook 测试
curl http://localhost:8001/github/test

# 查看 API 文档
# 浏览器访问: http://your-server-ip:8001/docs
```

## 功能状态

启动后的功能状态：

- ✅ **API 服务**: 运行在端口 8001
- ✅ **健康检查**: `/health` 端点
- ✅ **GitHub Webhook**: `/github/webhook` 端点
- ✅ **API 文档**: `/docs` 端点
- ✅ **Ping 事件处理**: 完全可用
- ⚠️ **Push 事件处理**: 需要 Redis 和 Celery
- ⚠️ **JaCoCo 扫描**: 需要 Docker

## 完整功能启动

要启用所有功能，请确保：

1. **Redis 运行**:
   ```bash
   docker run -d -p 6379:6379 redis:alpine
   ```

2. **Docker 可用**:
   ```bash
   docker --version
   ```

3. **构建 JaCoCo 扫描器镜像**:
   ```bash
   ./build-docker.sh
   ```

## 日志查看

```bash
# 查看 FastAPI 日志
tail -f logs/jacoco_api.log

# 查看 Celery 日志
tail -f logs/celery.log

# 查看实时日志
journalctl -f -u your-service-name
```

## 环境变量配置

编辑 `.env` 文件：

```env
# GitHub Webhook 密钥
GIT_WEBHOOK_SECRET=your_github_webhook_secret_here

# 调试模式
DEBUG=True

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# 日志级别
LOG_LEVEL=INFO
```

## 生产环境配置

### 使用 systemd 服务

1. 创建服务文件 `/etc/systemd/system/jacoco-api.service`:

```ini
[Unit]
Description=JaCoCo API Service
After=network.target

[Service]
Type=simple
User=automated
WorkingDirectory=/home/automated/project/jacocoApi
Environment=PATH=/home/automated/project/jacocoApi/venv/bin
ExecStart=/home/automated/project/jacocoApi/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

2. 启用和启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable jacoco-api
sudo systemctl start jacoco-api
sudo systemctl status jacoco-api
```

### 使用 nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /github/webhook {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 故障排除

### 如果仍然遇到 distutils 错误

```bash
# 安装 python3-distutils
sudo apt update
sudo apt install python3-distutils python3-dev

# 或者安装 setuptools
pip install setuptools>=68.0.0
```

### 如果 Celery 启动失败

```bash
# 检查 Redis 连接
redis-cli ping

# 检查 Python 路径
export PYTHONPATH=$PWD:$PYTHONPATH

# 重新启动 Celery
celery -A jacoco_tasks.celery_app worker --loglevel=info
```

### 如果端口被占用

```bash
# 查看端口使用情况
sudo netstat -tlnp | grep :8001

# 杀死占用端口的进程
sudo kill -9 <PID>

# 或使用不同端口
python3 -m uvicorn main:app --host 0.0.0.0 --port 8002
```

现在您的 Ubuntu 服务器应该可以成功启动 JaCoCo API 服务了！
