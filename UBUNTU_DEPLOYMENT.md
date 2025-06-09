# Ubuntu Linux 部署指南

## 🐧 部署方案选择

### 方案一：直接运行（推荐）

#### 系统要求
- Ubuntu 18.04+ 
- Python 3.8+
- MySQL 5.7+
- Git
- Maven 3.6+

#### 安装步骤

1. **安装系统依赖**
```bash
sudo apt update
sudo apt install -y python3 python3-pip git maven openjdk-11-jdk mysql-client
```

2. **克隆项目**
```bash
git clone <repository-url>
cd jacocoApi
```

3. **安装Python依赖**
```bash
pip3 install -r requirements.txt
```

4. **配置环境变量**
```bash
export CONFIG_STORAGE_TYPE=mysql
export MYSQL_HOST=172.16.1.30
export MYSQL_PORT=3306
export MYSQL_DATABASE=jacoco_config
export MYSQL_USER=jacoco
export MYSQL_PASSWORD=asd301325..
```

5. **启动服务**
```bash
python3 start.py
```

6. **验证部署**
```bash
curl http://localhost:8002/health
```

### 方案二：Docker部署

#### 构建API服务镜像
```bash
# 使用专用的API Dockerfile
docker build -f Dockerfile.api -t jacoco-api:ubuntu .
```

#### 运行容器
```bash
docker run -d \
  --name jacoco-api \
  -p 8002:8002 \
  -e CONFIG_STORAGE_TYPE=mysql \
  -e MYSQL_HOST=172.16.1.30 \
  -e MYSQL_USER=jacoco \
  -e MYSQL_PASSWORD=asd301325.. \
  jacoco-api:ubuntu
```

#### 查看日志
```bash
docker logs -f jacoco-api
```

### 方案三：Docker Compose部署

创建 `docker-compose.yml`:
```yaml
version: '3.8'

services:
  jacoco-api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8002:8002"
    environment:
      - CONFIG_STORAGE_TYPE=mysql
      - MYSQL_HOST=172.16.1.30
      - MYSQL_USER=jacoco
      - MYSQL_PASSWORD=asd301325..
    volumes:
      - ./reports:/app/reports
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

启动：
```bash
docker-compose up -d
```

## 🔧 系统服务配置

### 创建systemd服务（推荐）

1. **创建服务文件**
```bash
sudo nano /etc/systemd/system/jacoco-api.service
```

2. **服务配置内容**
```ini
[Unit]
Description=JaCoCo API Service
After=network.target mysql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/jacocoApi
Environment=CONFIG_STORAGE_TYPE=mysql
Environment=MYSQL_HOST=172.16.1.30
Environment=MYSQL_USER=jacoco
Environment=MYSQL_PASSWORD=asd301325..
ExecStart=/usr/bin/python3 start.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. **启用并启动服务**
```bash
sudo systemctl daemon-reload
sudo systemctl enable jacoco-api
sudo systemctl start jacoco-api
sudo systemctl status jacoco-api
```

## 🌐 Nginx反向代理（可选）

### 安装Nginx
```bash
sudo apt install nginx
```

### 配置反向代理
```bash
sudo nano /etc/nginx/sites-available/jacoco-api
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 启用配置
```bash
sudo ln -s /etc/nginx/sites-available/jacoco-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔍 故障排除

### 检查服务状态
```bash
# 直接运行
ps aux | grep python3

# systemd服务
sudo systemctl status jacoco-api
sudo journalctl -u jacoco-api -f

# Docker
docker ps
docker logs jacoco-api
```

### 检查端口占用
```bash
sudo netstat -tlnp | grep 8002
sudo ss -tlnp | grep 8002
```

### 检查MySQL连接
```bash
mysql -h 172.16.1.30 -u jacoco -p jacoco_config
```

## 📊 性能优化

### 系统优化
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# 优化网络参数
echo "net.core.somaxconn = 1024" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 应用优化
- 使用Gunicorn作为WSGI服务器
- 配置日志轮转
- 设置合适的工作进程数

## 🚀 生产环境建议

1. **使用systemd服务**：确保服务自动重启
2. **配置Nginx**：提供负载均衡和SSL终止
3. **监控日志**：使用logrotate管理日志文件
4. **备份配置**：定期备份MySQL数据库
5. **安全配置**：配置防火墙规则

## 📝 总结

- **推荐方案**：直接运行 + systemd服务
- **容器化**：使用Dockerfile.api构建专用镜像
- **生产环境**：systemd + Nginx + 监控
- **开发环境**：直接运行即可
