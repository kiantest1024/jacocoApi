# JaCoCo Scanner 使用说明

## 🐳 Docker扫描模式

### 优先级
1. **Docker扫描** (优先) - 使用隔离环境，性能更好
2. **本地扫描** (回退) - 当Docker不可用时自动切换

### Docker扫描特点
- ✅ 环境隔离，避免依赖冲突
- ✅ 性能优化，并发支持
- ✅ 自动构建镜像
- ✅ 超时保护 (5分钟)
- ✅ 自动回退机制

### 本地扫描特点
- ✅ 无需Docker环境
- ✅ 直接使用系统Maven
- ✅ 兼容性更好
- ⚠️ 可能有依赖冲突

## 🔧 配置说明

### Docker配置
```python
DEFAULT_SCAN_CONFIG = {
    "use_docker": True,              # 启用Docker扫描
    "docker_image": "jacoco-scanner:latest",
    "docker_timeout": 300,           # Docker扫描超时时间
    "force_local_scan": False,       # 是否强制本地扫描
}
```

### 强制本地扫描
如需禁用Docker扫描，设置：
```python
"force_local_scan": True
```

## 📊 扫描流程

1. **接收Webhook** → 解析仓库信息
2. **检查Docker** → 验证Docker环境
3. **Docker扫描** → 优先使用Docker
4. **本地回退** → Docker失败时自动切换
5. **生成报告** → XML/HTML格式
6. **发送通知** → Lark群组通知

## 🚀 性能优化

- Docker镜像复用，避免重复构建
- 并发扫描支持
- 智能超时机制
- 自动环境检测
- 资源清理机制

## 🛠️ 故障排除

### Docker问题
- 检查Docker服务是否运行
- 验证镜像是否构建成功
- 查看Docker日志

### 本地扫描问题
- 检查Maven环境
- 验证Java版本
- 查看项目依赖
