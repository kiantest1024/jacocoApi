# JaCoCo Scanner Docker Image
FROM openjdk:11-jdk-slim

# 安装必要的工具
RUN apt-get update && apt-get install -y \
    git \
    maven \
    curl \
    python3 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置工作目录
WORKDIR /app

# 创建必要的目录
RUN mkdir -p /app/scripts /app/reports /app/repos

# 复制扫描脚本
COPY scripts/ /app/scripts/

# 设置脚本执行权限
RUN chmod +x /app/scripts/*.sh

# 创建Maven配置目录并复制settings.xml
RUN mkdir -p /root/.m2
COPY scripts/settings.xml /root/.m2/settings.xml

# 设置环境变量 (移除已废弃的MaxPermSize参数)
ENV MAVEN_OPTS="-Xmx2g -XX:MetaspaceSize=512m"
ENV JAVA_OPTS="-Xmx2g"

# 默认命令
CMD ["/app/scripts/scan.sh"]
