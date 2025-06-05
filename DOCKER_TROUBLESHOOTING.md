# Docker故障排除指南

## 🐳 Docker问题诊断

### 1. Docker命令问题
**错误**: `exec: "--repo-url": executable file not found in $PATH`

**原因**: Docker容器的ENTRYPOINT配置错误

**解决方案**:
```bash
# 重新构建Docker镜像
./build_docker.sh
```

### 2. Docker未安装或不可用
**错误**: `Docker未安装或不可用`

**解决方案**:
- 安装Docker Desktop
- 启动Docker服务
- 或者使用本地扫描模式

### 3. Docker守护进程未运行
**错误**: `Docker守护进程未运行`

**解决方案**:
```bash
# Windows
启动Docker Desktop

# Linux
sudo systemctl start docker
```

### 4. Docker镜像构建失败
**可能原因**:
- 网络连接问题
- Dockerfile语法错误
- 依赖下载失败

**解决方案**:
```bash
# 清理Docker缓存
docker system prune -f

# 重新构建
docker build -t jacoco-scanner:latest .
```

## 🔄 自动回退机制

系统已配置智能回退：

1. **优先尝试Docker扫描**
   - 检查Docker是否可用
   - 检查镜像是否存在
   - 执行Docker扫描

2. **自动回退到本地扫描**
   - Docker不可用时自动切换
   - 使用系统Maven环境
   - 保证扫描功能可用

## 🛠️ 手动配置

### 强制使用本地扫描
在 `config.py` 中设置：
```python
DEFAULT_SCAN_CONFIG = {
    "force_local_scan": True,  # 强制本地扫描
    "use_docker": False,       # 禁用Docker
}
```

### 启用Docker扫描
```python
DEFAULT_SCAN_CONFIG = {
    "force_local_scan": False, # 允许Docker扫描
    "use_docker": True,        # 启用Docker
}
```

## 📊 扫描模式对比

| 特性 | Docker扫描 | 本地扫描 |
|------|------------|----------|
| 环境隔离 | ✅ 完全隔离 | ❌ 共享环境 |
| 依赖冲突 | ✅ 避免冲突 | ⚠️ 可能冲突 |
| 性能 | ✅ 优化配置 | ⚠️ 依赖环境 |
| 兼容性 | ⚠️ 需要Docker | ✅ 直接运行 |
| 维护成本 | ⚠️ 需要镜像管理 | ✅ 简单 |

## 🚀 推荐配置

### 生产环境
- 优先使用Docker扫描
- 配置自动回退
- 定期更新镜像

### 开发环境
- 可使用本地扫描
- 快速测试和调试
- 减少环境依赖

## 📝 日志分析

### 正常Docker扫描日志
```
[req_xxx] Docker环境可用，将使用Docker扫描
[req_xxx] 开始Docker JaCoCo扫描
[req_xxx] Docker扫描成功
```

### 回退到本地扫描日志
```
[req_xxx] Docker命令不可用，将使用本地扫描
[req_xxx] 使用本地扫描
[req_xxx] 开始本地JaCoCo扫描
```

### 错误日志
```
[req_xxx] Docker扫描失败，回退到本地扫描: [错误信息]
[req_xxx] 使用本地扫描
```
