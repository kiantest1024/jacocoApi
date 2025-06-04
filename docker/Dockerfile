# JaCoCo Scanner Docker Image
FROM openjdk:11-jdk-slim

# 安装必要的工具
RUN apt-get update && apt-get install -y \
    git \
    maven \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 创建必要的目录
RUN mkdir -p /app/scripts /app/reports /app/repos

# 复制扫描脚本
COPY scripts/ /app/scripts/

# 设置脚本执行权限
RUN chmod +x /app/scripts/*.sh

# 设置环境变量
ENV MAVEN_OPTS="-Xmx2g -XX:MaxPermSize=512m"
ENV JAVA_OPTS="-Xmx2g"

# 默认命令
CMD ["/app/scripts/scan.sh"]
