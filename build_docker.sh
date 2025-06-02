#!/bin/bash
# 构建 JaCoCo 扫描器 Docker 镜像

# 确保 jacoco-scanner 目录存在
mkdir -p jacoco-scanner

# 复制 jacoco-settings.xml 到 jacoco-scanner 目录
cp jacoco-settings.xml jacoco-scanner/

# 检查 pom.xml 是否存在于 jacoco-scanner 目录
if [ -f "jacoco-scanner/pom.xml" ]; then
    echo "pom.xml 已存在，无需复制"
else
    echo "正在创建 pom.xml 文件"
    cat > jacoco-scanner/pom.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.jacoco.scanner</groupId>
    <artifactId>jacoco-scanner</artifactId>
    <version>1.0.0</version>
    <packaging>pom</packaging>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <jacoco.version>0.8.11</jacoco.version>
    </properties>
</project>
EOF
fi

# 构建 Docker 镜像
echo "正在构建 jacoco-scanner-ci Docker 镜像..."
docker build -t jacoco-scanner-ci jacoco-scanner/

# 检查构建结果
if [ $? -eq 0 ]; then
    echo "Docker 镜像构建成功！"
    echo "镜像名称: jacoco-scanner-ci"
    echo "可以使用以下命令测试镜像:"
    echo "docker run --rm jacoco-scanner-ci mvn --version"
else
    echo "Docker 镜像构建失败！"
    exit 1
fi
