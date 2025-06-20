# JaCoCo 覆盖率为 0% - Linux 环境解决方案

## 环境确认

您提到已经在 Linux 上部署了 Maven，这很好！现在主要需要解决 Docker 环境问题。

## 快速诊断

首先运行诊断脚本确认当前状态：

```bash
cd jacocoApi
python3 diagnose.py
```

## 主要解决方案

### 方案 1: 修复 Docker 环境（推荐）

#### 1.1 检查 Docker 状态
```bash
# 检查 Docker 是否安装
docker --version

# 检查 Docker 服务状态
sudo systemctl status docker

# 如果未运行，启动 Docker
sudo systemctl start docker
sudo systemctl enable docker
```

#### 1.2 检查用户权限
```bash
# 检查当前用户是否在 docker 组中
groups | grep docker

# 如果不在，添加用户到 docker 组
sudo usermod -aG docker $USER

# 重新登录或运行
newgrp docker
```

#### 1.3 构建 JaCoCo 扫描器镜像
```bash
# 使用 Linux 构建脚本
chmod +x build-scanner.sh
./build-scanner.sh

# 或手动构建
docker build -f docker/Dockerfile.alpine -t jacoco-scanner:latest docker/
```

#### 1.4 验证镜像
```bash
docker images | grep jacoco-scanner
```

### 方案 2: 使用本地 Maven 扫描

如果 Docker 环境有问题，可以强制使用本地 Maven：

#### 2.1 验证 Maven 环境
```bash
mvn --version
echo $JAVA_HOME
```

#### 2.2 修改配置强制使用本地扫描
编辑 `config/config.py`：
```python
DEFAULT_SCAN_CONFIG = {
    "use_docker": False,        # 强制使用本地扫描
    "force_local_scan": True,
    # ... 其他配置保持不变
}
```

#### 2.3 测试本地扫描
```bash
# 手动测试项目
git clone http://172.16.1.30/kian/jacocotest.git test_project
cd test_project
mvn clean test jacoco:report
ls -la target/site/jacoco/
```

## 自动化修复工具

### 使用 Linux 专用修复脚本
```bash
chmod +x fix-jacoco-linux.sh
./fix-jacoco-linux.sh
```

这个脚本会：
1. 检查 Docker 环境并尝试修复
2. 验证 Maven 配置
3. 构建 JaCoCo 扫描器镜像
4. 测试扫描功能
5. 运行完整诊断

## 常见 Linux 环境问题

### 1. Docker 权限问题
```bash
# 症状：Got permission denied while trying to connect to the Docker daemon
# 解决：
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Docker 服务未启动
```bash
# 症状：Cannot connect to the Docker daemon
# 解决：
sudo systemctl start docker
sudo systemctl enable docker
```

### 3. 防火墙问题
```bash
# 如果无法访问 172.16.1.30
ping 172.16.1.30

# 检查防火墙设置
sudo ufw status
# 或
sudo firewall-cmd --list-all
```

### 4. Maven 内存设置
```bash
# 如果 Maven 构建内存不足
export MAVEN_OPTS="-Xmx2g -XX:MetaspaceSize=512m"
```

## 验证解决方案

### 1. 完整测试流程
```bash
# 1. 重新运行诊断
python3 diagnose.py

# 2. 测试 Docker 扫描
docker run --rm \
  -v "$(pwd)/temp_reports:/app/reports" \
  jacoco-scanner:latest \
  --repo-url http://172.16.1.30/kian/jacocotest.git \
  --commit-id main \
  --branch main \
  --service-name jacocotest

# 3. 检查报告
ls -la temp_reports/
cat temp_reports/jacoco.xml | grep -o 'covered="[0-9]*"'
```

### 2. 通过 API 测试
```bash
# 启动 JaCoCo API
cd jacocoApi
python3 app.py &

# 发送测试请求
curl -X POST http://localhost:8002/github/webhook-no-auth \
  -H "Content-Type: application/json" \
  -d '{
    "object_kind": "push",
    "project": {
      "name": "jacocotest", 
      "http_url": "http://172.16.1.30/kian/jacocotest.git"
    },
    "commits": [{"id": "main"}],
    "ref": "refs/heads/main"
  }'
```

## 预期结果

修复成功后，您应该看到：

1. **诊断结果**：
```
📊 诊断结果:
✅ Docker
✅ Maven  
✅ Git
✅ 配置
✅ 本地扫描
```

2. **扫描日志**：
```
[req_xxx] 使用Docker扫描
[req_xxx] JaCoCo XML parsing completed:
[req_xxx]   指令覆盖率: XX.XX%
[req_xxx]   分支覆盖率: XX.XX%
[req_xxx]   行覆盖率: XX.XX%
```

3. **生成的报告**：
- `reports/jacocotest/[commit]/jacoco.xml`
- `reports/jacocotest/[commit]/index.html`

## 系统要求

- **操作系统**: Linux (Ubuntu 18.04+, CentOS 7+, 等)
- **Docker**: 20.10+
- **Maven**: 3.6+
- **Java**: 11+
- **Python**: 3.6+
- **网络**: 能访问 172.16.1.30

## 故障排除

如果问题仍然存在：

1. **收集诊断信息**：
```bash
./fix-jacoco-linux.sh  # 选择选项 6 运行诊断
docker info
mvn --version
systemctl status docker
```

2. **检查日志**：
```bash
# JaCoCo API 日志
tail -f jacoco-api.log

# Docker 日志
sudo journalctl -u docker -f

# 系统日志
sudo journalctl -f
```

3. **手动测试项目**：
```bash
git clone http://172.16.1.30/kian/jacocotest.git
cd jacocotest
mvn clean test
find . -name "*.xml" -path "*/jacoco/*"
```

## 联系支持

如需进一步帮助，请提供：
- `python3 diagnose.py` 的完整输出
- `docker info` 输出
- `mvn --version` 输出
- JaCoCo API 的扫描日志

---

**Linux 环境优势**: 相比 Windows，Linux 环境下的 Docker 和 Maven 集成更稳定，问题通常更容易解决。
