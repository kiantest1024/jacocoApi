@echo off
REM 构建 JaCoCo 扫描器 Docker 镜像

REM 确保 jacoco-scanner 目录存在
if not exist jacoco-scanner mkdir jacoco-scanner

REM 复制 jacoco-settings.xml 到 jacoco-scanner 目录
copy jacoco-settings.xml jacoco-scanner\

REM 检查 pom.xml 是否存在于 jacoco-scanner 目录
if exist jacoco-scanner\pom.xml (
    echo pom.xml 已存在，无需复制
) else (
    echo 正在创建 pom.xml 文件
    type nul > jacoco-scanner\pom.xml
    echo ^<?xml version="1.0" encoding="UTF-8"?^> > jacoco-scanner\pom.xml
    echo ^<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"^> >> jacoco-scanner\pom.xml
    echo     ^<modelVersion^>4.0.0^</modelVersion^> >> jacoco-scanner\pom.xml
    echo     ^<groupId^>com.jacoco.scanner^</groupId^> >> jacoco-scanner\pom.xml
    echo     ^<artifactId^>jacoco-scanner^</artifactId^> >> jacoco-scanner\pom.xml
    echo     ^<version^>1.0.0^</version^> >> jacoco-scanner\pom.xml
    echo     ^<packaging^>pom^</packaging^> >> jacoco-scanner\pom.xml
    echo     ^<properties^> >> jacoco-scanner\pom.xml
    echo         ^<project.build.sourceEncoding^>UTF-8^</project.build.sourceEncoding^> >> jacoco-scanner\pom.xml
    echo         ^<maven.compiler.source^>11^</maven.compiler.source^> >> jacoco-scanner\pom.xml
    echo         ^<maven.compiler.target^>11^</maven.compiler.target^> >> jacoco-scanner\pom.xml
    echo         ^<jacoco.version^>0.8.11^</jacoco.version^> >> jacoco-scanner\pom.xml
    echo     ^</properties^> >> jacoco-scanner\pom.xml
    echo ^</project^> >> jacoco-scanner\pom.xml
)

REM 构建 Docker 镜像
echo 正在构建 jacoco-scanner-ci Docker 镜像...
docker build -t jacoco-scanner-ci jacoco-scanner\

REM 检查构建结果
if %ERRORLEVEL% EQU 0 (
    echo Docker 镜像构建成功！
    echo 镜像名称: jacoco-scanner-ci
    echo 可以使用以下命令测试镜像:
    echo docker run --rm jacoco-scanner-ci mvn --version
) else (
    echo Docker 镜像构建失败！
    exit /b 1
)
