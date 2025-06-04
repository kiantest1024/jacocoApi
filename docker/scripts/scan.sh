#!/bin/bash

# JaCoCo Docker扫描脚本
set -e

# 默认参数
REPO_URL=""
COMMIT_ID=""
BRANCH=""
SERVICE_NAME=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --repo-url)
            REPO_URL="$2"
            shift 2
            ;;
        --commit-id)
            COMMIT_ID="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --service-name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 验证必需参数
if [[ -z "$REPO_URL" || -z "$COMMIT_ID" || -z "$SERVICE_NAME" ]]; then
    echo "错误: 缺少必需参数"
    echo "用法: $0 --repo-url <URL> --commit-id <ID> --branch <BRANCH> --service-name <NAME>"
    exit 1
fi

echo "开始JaCoCo扫描..."
echo "仓库: $REPO_URL"
echo "提交: $COMMIT_ID"
echo "分支: $BRANCH"
echo "服务: $SERVICE_NAME"

# 设置路径
REPO_DIR="/app/repos/$SERVICE_NAME"
REPORTS_DIR="/app/reports"

# 创建目录
mkdir -p "$REPO_DIR"
mkdir -p "$REPORTS_DIR"

# 克隆或更新仓库
if [[ -d "$REPO_DIR/.git" ]]; then
    echo "更新现有仓库..."
    cd "$REPO_DIR"
    git fetch origin
    git reset --hard "$COMMIT_ID"
else
    echo "克隆仓库..."
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
    git checkout "$COMMIT_ID"
fi

# 检查是否为Maven项目
if [[ ! -f "pom.xml" ]]; then
    echo "错误: 不是Maven项目，未找到pom.xml"
    exit 1
fi

echo "找到Maven项目，开始增强pom.xml..."

# 增强pom.xml以支持JaCoCo
/app/scripts/enhance-pom.sh

echo "运行Maven测试和JaCoCo..."

# 设置Maven环境变量 (移除已废弃的MaxPermSize参数)
export MAVEN_OPTS="-Xmx2g -XX:MetaspaceSize=512m"
export JAVA_OPTS="-Xmx2g"

# 运行Maven命令
mvn clean compile test-compile test jacoco:report \
    -Dmaven.test.failure.ignore=true \
    -Dproject.build.sourceEncoding=UTF-8 \
    -Dmaven.compiler.source=11 \
    -Dmaven.compiler.target=11 \
    -Dmaven.resolver.transport=wagon \
    -Dmaven.wagon.http.retryHandler.count=3 \
    -Dmaven.wagon.http.pool=false \
    -U

# 检查并复制报告
if [[ -f "target/site/jacoco/jacoco.xml" ]]; then
    echo "复制JaCoCo XML报告..."
    cp "target/site/jacoco/jacoco.xml" "$REPORTS_DIR/"
fi

if [[ -d "target/site/jacoco" ]]; then
    echo "复制JaCoCo HTML报告..."
    cp -r "target/site/jacoco" "$REPORTS_DIR/html"
fi

# 生成摘要
/app/scripts/generate-summary.sh "$REPORTS_DIR"

echo "JaCoCo扫描完成"
