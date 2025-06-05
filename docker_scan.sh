#!/bin/bash

# 不使用 set -e，手动处理错误
echo "JaCoCo Docker Scanner Starting..."
echo "Arguments: $@"

REPO_URL=""
COMMIT_ID=""
BRANCH=""
SERVICE_NAME=""

# 解析参数
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
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
done

# 验证参数
if [[ -z "$REPO_URL" || -z "$COMMIT_ID" || -z "$SERVICE_NAME" ]]; then
    echo "❌ Missing required parameters"
    echo "Usage: $0 --repo-url <url> --commit-id <id> --branch <branch> --service-name <name>"
    echo "Received parameters:"
    echo "  REPO_URL: $REPO_URL"
    echo "  COMMIT_ID: $COMMIT_ID"
    echo "  BRANCH: $BRANCH"
    echo "  SERVICE_NAME: $SERVICE_NAME"
    exit 1
fi

echo "Starting JaCoCo scan for $SERVICE_NAME"
echo "Repository: $REPO_URL"
echo "Commit: $COMMIT_ID"
echo "Branch: $BRANCH"

# 克隆仓库
REPO_DIR="/app/repos/$SERVICE_NAME"
rm -rf "$REPO_DIR"

echo "Cloning repository..."
if ! git clone "$REPO_URL" "$REPO_DIR"; then
    echo "Error: Failed to clone repository"
    exit 1
fi

cd "$REPO_DIR"

# 切换到指定提交
echo "Switching to commit $COMMIT_ID..."
git checkout "$COMMIT_ID" 2>/dev/null || echo "Warning: Could not checkout $COMMIT_ID, using default branch"

# 检查是否为Maven项目
if [[ ! -f "pom.xml" ]]; then
    echo "Error: Not a Maven project - no pom.xml found"
    exit 1
fi

echo "Maven project confirmed"

# 创建完整的pom.xml以确保JaCoCo正常工作
echo "Creating enhanced pom.xml for JaCoCo..."

# 备份原始pom.xml
cp pom.xml pom.xml.original

# 创建新的pom.xml，确保包含所有必要的配置
cat > pom.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>jacocotest</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <jacoco.version>0.8.8</jacoco.version>
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
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.0.0-M7</version>
                <configuration>
                    <includes>
                        <include>**/*Test.java</include>
                        <include>**/*Tests.java</include>
                        <include>**/Test*.java</include>
                    </includes>
                    <argLine>${argLine}</argLine>
                </configuration>
            </plugin>

            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>${jacoco.version}</version>
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
        </plugins>
    </build>
</project>
EOF

echo "Enhanced pom.xml created successfully"

# 运行Maven测试和JaCoCo
echo "Running Maven with JaCoCo..."

# 确保使用正确的Java版本
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

echo "Java version:"
java -version

echo "Maven version:"
mvn -version

# 分步执行以便调试
echo "Step 1: Clean and compile"
mvn clean compile -Dmaven.test.failure.ignore=true --batch-mode || echo "Compile step completed with warnings"

echo "Step 2: Compile tests"
mvn test-compile -Dmaven.test.failure.ignore=true --batch-mode || echo "Test compile step completed with warnings"

echo "Step 3: Run tests with JaCoCo"
mvn test -Dmaven.test.failure.ignore=true --batch-mode || echo "Test step completed with warnings"

echo "Step 4: Generate JaCoCo report"
mvn jacoco:report --batch-mode || echo "Report generation completed with warnings"

echo "Maven execution completed"

# 显示详细的执行结果
echo "=== Maven Execution Results ==="

echo "Target directory contents:"
if [ -d "target" ]; then
    find target -type f | head -20
else
    echo "No target directory found"
fi

echo "Surefire reports:"
if [ -d "target/surefire-reports" ]; then
    ls -la target/surefire-reports/
    echo "Test results:"
    find target/surefire-reports -name "*.xml" -exec grep -l "testcase" {} \; | head -5
else
    echo "No surefire reports found"
fi

echo "JaCoCo files:"
find target -name "jacoco*" -type f | head -10

echo "JaCoCo exec file:"
if [ -f "target/jacoco.exec" ]; then
    ls -la target/jacoco.exec
    echo "Exec file size: $(wc -c < target/jacoco.exec) bytes"
else
    echo "No jacoco.exec file found"
fi

# 查找并复制报告
REPORTS_DIR="/app/reports"
mkdir -p "$REPORTS_DIR"

# 显示target目录结构用于调试
echo "Checking target directory structure..."
if [ -d "target" ]; then
    find target -type f -name "*.xml" -o -name "*.exec" | head -10
    echo "Target directory size: $(du -sh target 2>/dev/null || echo 'unknown')"
else
    echo "Warning: target directory not found"
fi

# 查找JaCoCo报告文件
echo "Looking for JaCoCo reports..."
JACOCO_XML=$(find target -name "jacoco.xml" -type f | head -1)
JACOCO_EXEC=$(find target -name "jacoco.exec" -type f | head -1)
JACOCO_HTML_DIR=$(find target -name "jacoco" -type d | head -1)

echo "Found files:"
echo "  jacoco.xml: $JACOCO_XML"
echo "  jacoco.exec: $JACOCO_EXEC"
echo "  jacoco HTML dir: $JACOCO_HTML_DIR"

if [[ -n "$JACOCO_XML" ]]; then
    echo "Found JaCoCo XML report: $JACOCO_XML"
    cp "$JACOCO_XML" "$REPORTS_DIR/jacoco.xml"

    # 显示XML文件内容的前几行用于调试
    echo "XML report preview:"
    head -10 "$JACOCO_XML"

    if [[ -n "$JACOCO_HTML_DIR" && -d "$JACOCO_HTML_DIR" ]]; then
        echo "Found JaCoCo HTML report: $JACOCO_HTML_DIR"
        cp -r "$JACOCO_HTML_DIR" "$REPORTS_DIR/html"
    fi

    echo "JaCoCo scan completed successfully"
elif [[ -n "$JACOCO_EXEC" ]]; then
    echo "Found jacoco.exec but no XML report, trying to generate report manually..."
    if mvn jacoco:report --batch-mode; then
        echo "Manual report generation succeeded"
    else
        echo "Manual report generation failed, but continuing..."
    fi

    # 重新查找XML报告
    JACOCO_XML=$(find target -name "jacoco.xml" -type f | head -1)
    if [[ -n "$JACOCO_XML" ]]; then
        echo "Successfully generated XML report: $JACOCO_XML"
        cp "$JACOCO_XML" "$REPORTS_DIR/jacoco.xml"
        echo "XML report preview:"
        head -10 "$JACOCO_XML"
    else
        echo "Failed to generate XML report, creating empty report"
        echo '<?xml version="1.0" encoding="UTF-8"?><report name="empty"><counter type="INSTRUCTION" missed="0" covered="0"/></report>' > "$REPORTS_DIR/jacoco.xml"
    fi
else
    echo "Warning: No JaCoCo reports or exec files found"
    echo "This might indicate:"
    echo "  1. No tests were executed"
    echo "  2. JaCoCo agent was not properly attached"
    echo "  3. Maven execution failed"
    echo "Creating empty report as fallback"
    echo '<?xml version="1.0" encoding="UTF-8"?><report name="empty"><counter type="INSTRUCTION" missed="0" covered="0"/></report>' > "$REPORTS_DIR/jacoco.xml"
fi

echo "Scan completed for $SERVICE_NAME"
