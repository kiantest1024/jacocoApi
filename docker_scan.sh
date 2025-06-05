#!/bin/bash

set -e

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
git clone "$REPO_URL" "$REPO_DIR"
cd "$REPO_DIR"

# 切换到指定提交
git checkout "$COMMIT_ID" || echo "Warning: Could not checkout $COMMIT_ID"

# 检查是否为Maven项目
if [[ ! -f "pom.xml" ]]; then
    echo "Error: Not a Maven project"
    exit 1
fi

# 简单的pom.xml增强 - 添加JaCoCo插件
echo "Enhancing pom.xml for JaCoCo..."

# 检查是否已有JaCoCo插件
if grep -q "jacoco-maven-plugin" pom.xml; then
    echo "JaCoCo plugin already exists in pom.xml"
else
    echo "Adding JaCoCo plugin to pom.xml..."

    # 创建临时的插件配置
    cat > jacoco_plugin.xml << 'EOF'
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>0.8.8</version>
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
                <configuration>
                    <outputDirectory>${project.reporting.outputDirectory}/jacoco</outputDirectory>
                </configuration>
            </plugin>
EOF

    # 如果没有plugins标签，添加整个build/plugins结构
    if ! grep -q "<plugins>" pom.xml; then
        if ! grep -q "<build>" pom.xml; then
            # 在</project>前添加build部分
            sed -i '/<\/project>/i\    <build>\n        <plugins>' pom.xml
            cat jacoco_plugin.xml >> pom.xml
            echo "        </plugins>" >> pom.xml
            echo "    </build>" >> pom.xml
        else
            # 在</build>前添加plugins部分
            sed -i '/<\/build>/i\        <plugins>' pom.xml
            sed -i '/<\/build>/i\        </plugins>' pom.xml
            sed -i '/        <plugins>/r jacoco_plugin.xml' pom.xml
        fi
    else
        # 在</plugins>前添加插件
        sed -i '/<\/plugins>/i\' pom.xml
        sed -i '/<\/plugins>/r jacoco_plugin.xml' pom.xml
    fi

    rm -f jacoco_plugin.xml
    echo "JaCoCo plugin added successfully"
fi

# 运行Maven测试和JaCoCo
echo "Running Maven test with JaCoCo..."

# 首先编译项目
echo "Compiling project..."
mvn clean compile \
    -Dmaven.test.failure.ignore=true \
    -Dproject.build.sourceEncoding=UTF-8 \
    -Dmaven.compiler.source=11 \
    -Dmaven.compiler.target=11 \
    --batch-mode

# 运行测试
echo "Running tests..."
mvn test \
    -Dmaven.test.failure.ignore=true \
    -Dproject.build.sourceEncoding=UTF-8 \
    --batch-mode

# 生成JaCoCo报告
echo "Generating JaCoCo report..."
mvn jacoco:report \
    -Dmaven.test.failure.ignore=true \
    --batch-mode

echo "Maven execution completed"

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
    mvn jacoco:report --batch-mode || echo "Manual report generation failed"

    # 重新查找XML报告
    JACOCO_XML=$(find target -name "jacoco.xml" -type f | head -1)
    if [[ -n "$JACOCO_XML" ]]; then
        echo "Successfully generated XML report: $JACOCO_XML"
        cp "$JACOCO_XML" "$REPORTS_DIR/jacoco.xml"
        head -10 "$JACOCO_XML"
    else
        echo "Failed to generate XML report, creating empty report"
        echo '<?xml version="1.0" encoding="UTF-8"?><report name="empty"><counter type="INSTRUCTION" missed="0" covered="0"/></report>' > "$REPORTS_DIR/jacoco.xml"
    fi
else
    echo "Warning: No JaCoCo reports or exec files found"
    echo "Creating empty report"
    echo '<?xml version="1.0" encoding="UTF-8"?><report name="empty"><counter type="INSTRUCTION" missed="0" covered="0"/></report>' > "$REPORTS_DIR/jacoco.xml"
fi

echo "Scan completed for $SERVICE_NAME"
