# Linux环境问题排查和解决指南

## 🎯 问题描述

在Linux环境中运行JaCoCo API时遇到的常见问题：
1. **数据不一致**: Linux和Windows环境显示不同的配置数据
2. **通知失败**: GitLab webhook触发后没有发送Lark通知
3. **报告缺失**: 没有生成HTML报告

## 🔍 问题原因分析

### 1. 数据不一致问题
- **原因**: Windows使用文件配置，Linux使用MySQL配置
- **表现**: 两个环境显示不同的机器人和项目映射

### 2. 通知失败问题
- **原因**: 环境变量未正确设置，或MySQL连接失败
- **表现**: webhook处理成功但没有发送通知

### 3. 报告缺失问题
- **原因**: Git/Maven/Docker环境配置问题
- **表现**: 扫描失败或报告生成失败

## 🔧 解决方案

### 方案一：快速修复（推荐）

1. **设置环境变量**
```bash
export CONFIG_STORAGE_TYPE=mysql
export MYSQL_HOST=172.16.1.30
export MYSQL_USER=jacoco
export MYSQL_PASSWORD=asd301325..
export MYSQL_DATABASE=jacoco_config
```

2. **启动服务**
```bash
python3 app.py
```

3. **运行修复脚本**
```bash
python3 quick_fix_linux.py
```

### 方案二：完整配置

1. **复制环境配置**
```bash
cp .env.example .env
# 编辑 .env 文件，确保MySQL配置正确
```

2. **运行配置脚本**
```bash
chmod +x setup_linux_env.sh
./setup_linux_env.sh
```

3. **验证配置**
```bash
python3 linux_debug.py
```

## 📋 详细排查步骤

### 1. 检查环境变量
```bash
echo $CONFIG_STORAGE_TYPE
echo $MYSQL_HOST
echo $MYSQL_USER
```

### 2. 测试MySQL连接
```bash
mysql -h 172.16.1.30 -u jacoco -p jacoco_config
# 输入密码: asd301325..
```

### 3. 检查服务状态
```bash
curl http://localhost:8002/health
curl http://localhost:8002/config/status
```

### 4. 查看服务日志
```bash
tail -f logs/jacoco-api.log
```

### 5. 测试webhook
```bash
curl -X POST http://localhost:8002/github/webhook-no-auth \
  -H "Content-Type: application/json" \
  -H "X-Gitlab-Event: Push Hook" \
  -d '{
    "object_kind": "push",
    "project": {
      "name": "jacocotest",
      "git_http_url": "http://172.16.1.30/kian/jacocotest.git"
    },
    "commits": [{"id": "test123", "message": "test"}]
  }'
```

## 🛠️ 常见问题解决

### 问题1: MySQL连接失败
```
错误: Can't connect to MySQL server
```

**解决方案:**
1. 检查MySQL服务是否运行
2. 检查网络连接
3. 验证用户名密码
4. 检查防火墙设置

### 问题2: Git命令失败
```
错误: git: command not found
```

**解决方案:**
```bash
sudo apt update
sudo apt install git
```

### 问题3: Maven命令失败
```
错误: mvn: command not found
```

**解决方案:**
```bash
sudo apt install maven
```

### 问题4: Docker命令失败
```
错误: docker: command not found
```

**解决方案:**
```bash
sudo apt install docker.io
sudo systemctl start docker
sudo usermod -aG docker $USER
# 重新登录或运行: newgrp docker
```

### 问题5: Java环境问题
```
错误: JAVA_HOME not set
```

**解决方案:**
```bash
sudo apt install openjdk-11-jdk
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
echo 'export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64' >> ~/.bashrc
```

### 问题6: 权限问题
```
错误: Permission denied
```

**解决方案:**
```bash
chmod +x *.sh
chmod 755 reports logs temp
```

## 🧪 测试验证

### 1. 验证配置同步
访问Web界面检查数据是否一致：
```
http://localhost:8002/config
```

### 2. 验证webhook功能
在GitLab项目中推送代码，检查：
- GitLab webhook日志
- JaCoCo API服务日志
- Lark机器人通知

### 3. 验证报告生成
检查reports目录是否有HTML报告文件：
```bash
ls -la reports/
```

## 📊 监控和维护

### 1. 服务监控
```bash
# 检查进程
ps aux | grep python

# 检查端口
netstat -tlnp | grep 8002

# 检查日志
tail -f logs/jacoco-api.log
```

### 2. 数据库监控
```bash
mysql -h 172.16.1.30 -u jacoco -p jacoco_config -e "
SELECT COUNT(*) as project_count FROM project_mappings;
SELECT COUNT(*) as bot_count FROM lark_bots;
"
```

### 3. 定期维护
```bash
# 清理旧报告
find reports/ -name "*.html" -mtime +30 -delete

# 清理日志
logrotate /etc/logrotate.d/jacoco-api
```

## 🚀 生产环境建议

### 1. 使用systemd服务
```bash
sudo cp jacoco-api.service /etc/systemd/system/
sudo systemctl enable jacoco-api
sudo systemctl start jacoco-api
```

### 2. 配置Nginx反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 设置日志轮转
```bash
sudo tee /etc/logrotate.d/jacoco-api << EOF
/path/to/jacoco/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
```

## 📞 获取帮助

如果问题仍然存在，请提供以下信息：
1. 操作系统版本: `cat /etc/os-release`
2. Python版本: `python3 --version`
3. 服务日志: `tail -50 logs/jacoco-api.log`
4. 环境变量: `env | grep -E "(CONFIG|MYSQL)"`
5. 错误信息的完整截图
