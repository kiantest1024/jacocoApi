FROM openjdk:11-jdk-slim

# 安装必要工具
RUN apt-get update && apt-get install -y \
    git \
    maven \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 创建必要目录
RUN mkdir -p /app/repos /app/reports /app/scripts

# 复制扫描脚本
COPY docker_scan.sh /app/scripts/docker_scan.sh
RUN chmod +x /app/scripts/docker_scan.sh

# 安装Python3（用于pom.xml增强）
RUN apt-get update && apt-get install -y python3 && rm -rf /var/lib/apt/lists/*

# 设置Maven配置优化
ENV MAVEN_OPTS="-Xmx1024m -XX:MaxPermSize=256m"
ENV MAVEN_CONFIG="/root/.m2"

# 预下载常用Maven依赖
RUN mvn help:evaluate -Dexpression=maven.version -q -DforceStdout || true

# 入口点
ENTRYPOINT ["/bin/bash", "/app/scripts/docker_scan.sh"]
