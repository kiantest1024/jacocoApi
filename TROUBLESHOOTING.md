# JaCoCo 覆盖率为 0% 问题排查指南

## 问题描述

使用 JaCoCo API 扫描 `http://172.16.1.30/kian/jacocotest.git` 项目时，覆盖率显示为 0%，但项目本来是有覆盖率的。

## 常见原因分析

### 1. Docker 环境问题 🐳

**症状**: 扫描日志显示 "Docker镜像不存在，使用本地扫描"

**原因**: 
- Docker Desktop 未启动
- `jacoco-scanner:latest` 镜像不存在

**解决方案**:
```bash
# 1. 启动 Docker Desktop
# 2. 构建 JaCoCo 扫描器镜像
bash build-scanner.sh
```

### 2. 项目测试代码问题 📝

**症状**: 扫描完成但覆盖率为 0%

**原因**:
- 项目没有单元测试
- 测试代码路径不正确
- 测试无法正常运行

**检查方法**:
```bash
# 检查测试代码是否存在
find src/test -name "*.java" 2>/dev/null

# 手动运行测试
mvn test
```

### 3. Maven 配置问题 📦

**症状**: Maven 构建失败或 JaCoCo 插件未执行

**原因**:
- pom.xml 缺少 JaCoCo 插件配置
- 父 POM 依赖问题
- Maven 版本兼容性问题

**解决方案**: 系统会自动增强 pom.xml 添加 JaCoCo 配置

### 4. 网络连接问题 🌐

**症状**: 无法克隆仓库

**原因**:
- 无法访问 172.16.1.30
- Git 认证问题

**检查方法**:
```bash
# 测试网络连接
ping 172.16.1.30

# 测试仓库克隆
git clone http://172.16.1.30/kian/jacocotest.git
```

## 快速诊断工具

### 1. 运行诊断脚本
```bash
python3 diagnose.py
```

### 2. 使用修复工具
```bash
bash fix-jacoco.sh
```

### 3. 手动检查步骤

#### 步骤 1: 检查 Docker
```bash
docker --version
docker info
docker images | grep jacoco-scanner
```

#### 步骤 2: 检查项目结构
```bash
git clone http://172.16.1.30/kian/jacocotest.git
cd jacocotest
ls -la src/test/java/  # 检查测试代码
```

#### 步骤 3: 手动运行 Maven 测试
```bash
mvn clean test
mvn jacoco:report
ls -la target/site/jacoco/  # 检查报告生成
```

## 解决方案

### 方案 1: 构建 Docker 镜像（推荐）

```bash
# 1. 确保 Docker Desktop 运行
# 2. 构建扫描器镜像
bash build-scanner.sh

# 3. 验证镜像
docker images | grep jacoco-scanner
```

### 方案 2: 修复本地扫描环境

```bash
# 1. 安装 Maven
# Windows: 下载并配置环境变量
# Linux/Mac: sudo apt install maven 或 brew install maven

# 2. 验证 Maven
mvn --version

# 3. 测试本地扫描
python3 diagnose.py
```

### 方案 3: 检查项目测试代码

如果项目确实没有测试代码，需要：

1. **添加测试代码**: 在 `src/test/java` 目录下添加单元测试
2. **确保测试可运行**: `mvn test` 应该能成功执行
3. **验证 JaCoCo 配置**: 确保 pom.xml 包含 JaCoCo 插件

### 方案 4: 强制使用本地扫描

如果 Docker 环境有问题，可以修改配置强制使用本地扫描：

```python
# 在 config/config.py 中设置
DEFAULT_SCAN_CONFIG = {
    "use_docker": False,  # 强制使用本地扫描
    "force_local_scan": True,
    # ... 其他配置
}
```

## 验证修复结果

### 1. 通过 API 测试
```bash
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

### 2. 检查报告生成
```bash
ls -la reports/jacocotest/
```

### 3. 查看日志
检查 JaCoCo API 日志，确认扫描过程没有错误。

## 预防措施

1. **定期检查 Docker 环境**: 确保 Docker Desktop 正常运行
2. **维护测试代码**: 确保项目包含有效的单元测试
3. **监控扫描日志**: 及时发现和解决扫描问题
4. **备份配置**: 定期备份 JaCoCo API 配置

## 联系支持

如果问题仍然存在，请提供以下信息：

1. 诊断脚本输出: `python3 diagnose.py`
2. JaCoCo API 日志
3. 项目结构: `tree src/` 或 `find src/ -name "*.java"`
4. Maven 测试输出: `mvn test`

---

**最后更新**: 2025-06-20
**版本**: 1.0
