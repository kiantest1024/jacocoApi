#!/bin/bash

# JaCoCo Docker扫描脚本 - Enhanced Version
set -e

# 启用详细日志
set -x

# 默认参数
REPO_URL=""
COMMIT_ID=""
BRANCH=""
SERVICE_NAME=""

# 日志函数
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1"
}

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

# 简单增强pom.xml以支持JaCoCo（使用字符串替换方法）
echo "备份原始pom.xml..."
cp pom.xml pom.xml.backup

echo "检查并添加JaCoCo配置..."

# 检查是否已有JaCoCo插件
if grep -q "jacoco-maven-plugin" pom.xml; then
    echo "JaCoCo插件已存在，跳过增强"
else
    echo "添加JaCoCo插件..."

    # 添加JaCoCo属性
    if grep -q "<properties>" pom.xml; then
        sed -i 's|<properties>|<properties>\n        <jacoco.version>0.8.7</jacoco.version>|' pom.xml
    fi

    # 添加JaCoCo插件
    if grep -q "<plugins>" pom.xml; then
        sed -i 's|<plugins>|<plugins>\n            <plugin>\n                <groupId>org.jacoco</groupId>\n                <artifactId>jacoco-maven-plugin</artifactId>\n                <version>0.8.7</version>\n                <executions>\n                    <execution>\n                        <id>prepare-agent</id>\n                        <goals>\n                            <goal>prepare-agent</goal>\n                        </goals>\n                    </execution>\n                    <execution>\n                        <id>report</id>\n                        <phase>test</phase>\n                        <goals>\n                            <goal>report</goal>\n                        </goals>\n                    </execution>\n                </executions>\n            </plugin>|' pom.xml
    fi
fi

echo "运行Maven测试和JaCoCo..."

# 设置Maven环境变量 (移除已废弃的MaxPermSize参数)
export MAVEN_OPTS="-Xmx2g -XX:MetaspaceSize=512m"
export JAVA_OPTS="-Xmx2g"

# 运行Maven命令
echo "尝试标准Maven扫描..."
mvn clean compile test-compile test jacoco:report \
    -Dmaven.test.failure.ignore=true \
    -Dproject.build.sourceEncoding=UTF-8 \
    -Dmaven.compiler.source=11 \
    -Dmaven.compiler.target=11 \
    -Dmaven.resolver.transport=wagon \
    -Dmaven.wagon.http.retryHandler.count=3 \
    -Dmaven.wagon.http.pool=false \
    -U

# 检查是否成功
if [ $? -ne 0 ]; then
    echo "标准Maven扫描失败，检查是否为父POM问题..."

    # 检查是否是父POM问题 - 检查Maven输出
    if mvn help:effective-pom 2>&1 | grep -q "Non-resolvable parent POM"; then

        echo "检测到父POM问题，尝试创建独立pom.xml..."

        # 提取基本信息
        GROUP_ID=$(grep -o '<groupId>[^<]*</groupId>' pom.xml | head -1 | sed 's/<[^>]*>//g')
        ARTIFACT_ID=$(grep -o '<artifactId>[^<]*</artifactId>' pom.xml | head -1 | sed 's/<[^>]*>//g')
        VERSION=$(grep -o '<version>[^<]*</version>' pom.xml | head -1 | sed 's/<[^>]*>//g')

        # 设置默认值
        GROUP_ID=${GROUP_ID:-"com.example"}
        ARTIFACT_ID=${ARTIFACT_ID:-"test-project"}
        VERSION=${VERSION:-"1.0.0"}

        echo "创建独立pom.xml: $GROUP_ID:$ARTIFACT_ID:$VERSION"

        # 创建独立的pom.xml
        cat > pom.xml << EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>$GROUP_ID</groupId>
    <artifactId>$ARTIFACT_ID</artifactId>
    <version>$VERSION</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <jacoco.version>0.8.7</jacoco.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.8.1</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>\${jacoco.version}</version>
                <executions>
                    <execution>
                        <id>prepare-agent</id>
                        <goals>
                            <goal>prepare-agent</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>report</id>
                        <phase>test</phase>
                        <goals>
                            <goal>report</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.0.0-M5</version>
                <configuration>
                    <testFailureIgnore>true</testFailureIgnore>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
EOF

        echo "使用独立pom.xml重新扫描..."
        mvn clean compile test-compile test jacoco:report \
            -Dmaven.test.failure.ignore=true \
            -Dproject.build.sourceEncoding=UTF-8 \
            -Dmaven.compiler.source=11 \
            -Dmaven.compiler.target=11
    fi
fi

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
if [[ -f "/app/scripts/generate-summary.sh" ]]; then
    /app/scripts/generate-summary.sh "$REPORTS_DIR"
else
    echo "警告: 未找到 generate-summary.sh 脚本"
fi

echo "JaCoCo扫描完成"
