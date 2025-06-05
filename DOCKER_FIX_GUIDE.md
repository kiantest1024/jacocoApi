# Docker修复指南

## 🔧 问题诊断

### 当前问题
Docker镜像的ENTRYPOINT配置有问题，导致容器无法正确启动。

### 错误信息
```
exec: "--help": executable file not found in $PATH: unknown
```

## 🛠️ 修复步骤

### 1. 重建Docker镜像
```bash
# 删除旧镜像
docker rmi jacoco-scanner:latest

# 重新构建
docker build -t jacoco-scanner:latest .
```

### 2. 测试镜像启动
```bash
# 测试基本启动（应该显示用法信息）
docker run --rm jacoco-scanner:latest

# 测试完整扫描
docker run --rm -v /tmp/test_reports:/app/reports jacoco-scanner:latest \
  --repo-url http://172.16.1.30/kian/jacocotest.git \
  --commit-id 5ea76b4989a17153eade57d7d55609ebad7fdd9e \
  --branch main \
  --service-name jacocotest
```

### 3. 验证修复
如果看到以下输出，说明修复成功：
```
Docker Container Starting...
Received arguments: ...
Usage: docker run jacoco-scanner:latest --repo-url <url> --commit-id <id> --branch <branch> --service-name <name>
```

## 🔍 故障排除

### 如果构建失败
1. 检查Docker守护进程是否运行
2. 检查网络连接
3. 清理Docker缓存：`docker system prune -f`

### 如果启动失败
1. 检查脚本权限：`docker run --rm jacoco-scanner:latest ls -la /app/`
2. 检查bash路径：`docker run --rm jacoco-scanner:latest which bash`
3. 手动执行脚本：`docker run --rm jacoco-scanner:latest /bin/bash /app/entrypoint.sh`

## 📋 修复内容

### 1. 创建了包装脚本
- `entrypoint.sh` - Docker容器入口点包装脚本
- 处理参数验证和脚本调用

### 2. 修改了Dockerfile
- 使用 `/bin/bash` 明确指定bash路径
- 复制并设置包装脚本权限
- 使用包装脚本作为ENTRYPOINT

### 3. 更新了测试脚本
- `fix_docker.py` - 自动修复脚本
- `quick_test.sh` - 快速测试脚本

## ✅ 预期结果

修复后，Docker扫描应该能够正常工作：
1. 容器能够正确启动
2. 参数能够正确传递
3. JaCoCo扫描能够正常执行
4. 报告能够正确生成
