# Docker部署故障排除指南

## 🔧 常见问题及解决方案

### 1. Java包安装失败

#### 问题
```
E: Unable to locate package openjdk-11-jdk
```

#### 解决方案
项目提供了两个Dockerfile版本：

**方案A: 使用修复后的Debian版本**
```bash
docker build -f Dockerfile.service -t jacoco-scanner-api .
```

**方案B: 使用Ubuntu版本**
```bash
docker build -f Dockerfile.ubuntu -t jacoco-scanner-api .
```

**自动选择**: 快速部署脚本会自动尝试两个版本
```bash
./quick-deploy.sh
```

### 2. 端口占用问题

#### 问题
```
Error: Port 8002 is already in use
```

#### 解决方案
```bash
# 查看占用端口的进程
docker ps | grep 8002

# 停止现有容器
docker stop jacoco-scanner-api

# 或使用不同端口
docker run -d -p 8003:8002 --name jacoco-scanner-api jacoco-scanner-api
```

### 3. Docker权限问题

#### 问题
```
Permission denied while trying to connect to Docker daemon
```

#### 解决方案
```bash
# 添加用户到docker组
sudo usermod -aG docker $USER

# 重新登录或重启终端
newgrp docker

# 或使用sudo运行
sudo ./quick-deploy.sh
```

### 4. 镜像构建缓存问题

#### 问题
构建过程中出现缓存相关错误

#### 解决方案
```bash
# 清理Docker缓存
docker system prune -f

# 强制重新构建
docker build --no-cache -f Dockerfile.service -t jacoco-scanner-api .
```

### 5. 容器启动失败

#### 问题
容器启动后立即退出

#### 解决方案
```bash
# 查看容器日志
docker logs jacoco-scanner-api

# 交互式启动调试
docker run -it --rm jacoco-scanner-api /bin/bash

# 检查健康状态
docker inspect jacoco-scanner-api | grep Health
```

## 🧪 测试命令

### 验证Docker环境
```bash
# 检查Docker版本
docker --version

# 检查Docker服务状态
docker info

# 测试Docker运行
docker run hello-world
```

### 验证镜像构建
```bash
# 运行构建测试
./test-docker-deploy.sh

# 手动测试构建
docker build -f Dockerfile.service -t test-image .
docker rmi test-image
```

### 验证服务运行
```bash
# 检查服务状态
curl http://localhost:8002/health

# 检查API文档
curl http://localhost:8002/docs

# 查看容器资源使用
docker stats jacoco-scanner-api
```

## 🔍 调试技巧

### 1. 进入运行中的容器
```bash
docker exec -it jacoco-scanner-api /bin/bash
```

### 2. 查看详细日志
```bash
# 实时日志
docker logs -f jacoco-scanner-api

# 最近100行日志
docker logs --tail 100 jacoco-scanner-api
```

### 3. 检查环境变量
```bash
docker exec jacoco-scanner-api env
```

### 4. 检查Java和Maven
```bash
docker exec jacoco-scanner-api java -version
docker exec jacoco-scanner-api mvn -version
```

## 🚀 性能优化

### 1. 减少镜像大小
- 使用多阶段构建
- 清理包管理器缓存
- 删除不必要的文件

### 2. 加速构建
- 使用构建缓存
- 优化Dockerfile层顺序
- 使用.dockerignore

### 3. 运行时优化
- 设置合适的内存限制
- 配置健康检查
- 使用重启策略

## 📞 获取帮助

如果问题仍然存在：

1. **查看日志**: `docker logs jacoco-scanner-api`
2. **检查系统**: `docker system df`
3. **重新部署**: `./deploy.sh`
4. **清理重建**: `docker system prune && ./quick-deploy.sh`
