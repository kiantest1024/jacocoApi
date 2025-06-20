# JaCoCo 覆盖率为 0% 问题解决方案

## 问题确认

根据诊断结果，您的 JaCoCo 扫描覆盖率为 0% 的主要原因是：

1. ❌ **Docker 服务未运行** - 导致无法使用 Docker 扫描
2. ❌ **Maven 未安装** - 导致本地扫描失败
3. ✅ **项目本身正常** - 有主代码和测试代码

## 立即解决方案

### 方案 1: 使用 Docker 扫描（推荐）

#### 步骤 1: 启动 Docker Desktop
1. 打开 Docker Desktop 应用程序
2. 等待 Docker 服务完全启动
3. 确认 Docker 图标显示为绿色

#### 步骤 2: 构建 JaCoCo 扫描器镜像
```cmd
# 在 jacocoApi 目录下运行
build-scanner.bat
```

或者手动构建：
```cmd
docker build -f docker\Dockerfile.alpine -t jacoco-scanner:latest docker\
```

#### 步骤 3: 验证镜像构建
```cmd
docker images | findstr jacoco-scanner
```

应该看到类似输出：
```
jacoco-scanner   latest   abc123def456   2 minutes ago   500MB
```

### 方案 2: 安装 Maven 支持本地扫描

#### 下载和安装 Maven
1. 访问 https://maven.apache.org/download.cgi
2. 下载 `apache-maven-3.9.x-bin.zip`
3. 解压到 `C:\Program Files\Apache\maven`
4. 添加环境变量：
   - `MAVEN_HOME`: `C:\Program Files\Apache\maven`
   - `PATH`: 添加 `%MAVEN_HOME%\bin`

#### 验证安装
```cmd
mvn --version
```

## 测试解决方案

### 重新运行诊断
```cmd
python jacocoApi\diagnose.py
```

期望结果：
```
📊 诊断结果:
✅ Docker
✅ Maven (或 ❌ 如果选择只用 Docker)
✅ Git
✅ 配置
✅ 本地扫描
```

### 测试 JaCoCo 扫描

#### 方法 1: 通过 API 测试
启动 JaCoCo API 服务：
```cmd
cd jacocoApi
python app.py
```

发送测试请求：
```cmd
curl -X POST http://localhost:8002/github/webhook-no-auth ^
  -H "Content-Type: application/json" ^
  -d "{\"object_kind\": \"push\", \"project\": {\"name\": \"jacocotest\", \"http_url\": \"http://172.16.1.30/kian/jacocotest.git\"}, \"commits\": [{\"id\": \"main\"}], \"ref\": \"refs/heads/main\"}"
```

#### 方法 2: 手动测试 Docker 扫描
```cmd
# 创建临时目录用于报告
mkdir temp_reports

# 运行 Docker 扫描
docker run --rm -v "%CD%\temp_reports:/app/reports" jacoco-scanner:latest ^
  --repo-url http://172.16.1.30/kian/jacocotest.git ^
  --commit-id main ^
  --branch main ^
  --service-name jacocotest

# 检查报告
dir temp_reports
```

## 预期结果

成功解决后，您应该看到：

1. **扫描日志显示**：
   ```
   [req_xxx] 使用Docker扫描
   [req_xxx] JaCoCo XML parsing completed:
   [req_xxx]   指令覆盖率: XX.XX%
   [req_xxx]   分支覆盖率: XX.XX%
   [req_xxx]   行覆盖率: XX.XX%
   ```

2. **生成的报告文件**：
   - `reports/jacocotest/[commit]/jacoco.xml`
   - `reports/jacocotest/[commit]/index.html`

3. **Lark 通知**（如果配置了）：
   包含实际的覆盖率数据而不是 0%

## 故障排除

### 如果 Docker 构建失败
```cmd
# 检查 Docker 日志
docker build -f docker\Dockerfile.alpine -t jacoco-scanner:latest docker\ --no-cache

# 检查文件权限
dir docker\scripts\
```

### 如果扫描仍然返回 0%
1. **检查项目测试**：
   ```cmd
   git clone http://172.16.1.30/kian/jacocotest.git
   cd jacocotest
   mvn test
   ```

2. **检查 JaCoCo 配置**：
   确认 pom.xml 包含 JaCoCo 插件配置

3. **查看详细日志**：
   检查 JaCoCo API 的完整日志输出

### 如果网络问题
```cmd
# 测试网络连接
ping 172.16.1.30

# 测试仓库访问
git clone http://172.16.1.30/kian/jacocotest.git test_clone
```

## 验证成功

运行以下命令验证一切正常：

```cmd
# 1. 检查 Docker
docker images | findstr jacoco-scanner

# 2. 重新诊断
python jacocoApi\diagnose.py

# 3. 测试扫描
# (使用上面的 API 测试方法)
```

## 联系支持

如果问题仍然存在，请提供：
1. 诊断脚本的完整输出
2. Docker 构建日志
3. JaCoCo API 扫描日志
4. 项目的 `mvn test` 输出

---

**重要提示**: 确保 Docker Desktop 始终在运行状态，这是解决覆盖率为 0% 问题的关键。
