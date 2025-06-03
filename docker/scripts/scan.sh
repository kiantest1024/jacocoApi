#!/bin/bash

# JaCoCo 扫描脚本
# 在 Docker 容器中执行 Java 项目的 JaCoCo 覆盖率扫描

set -e

# 默认参数
REPO_URL=""
COMMIT_ID=""
BRANCH_NAME="main"
PROJECT_PATH="/app/repos/jacocoTest"
REPORTS_PATH="/app/reports"
CONFIG_PATH="/app/configs"

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
            BRANCH_NAME="$2"
            shift 2
            ;;
        --project-path)
            PROJECT_PATH="$2"
            shift 2
            ;;
        --reports-path)
            REPORTS_PATH="$2"
            shift 2
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 验证必需参数
if [[ -z "$REPO_URL" ]]; then
    echo "错误: 必须提供 --repo-url 参数"
    exit 1
fi

if [[ -z "$COMMIT_ID" ]]; then
    echo "错误: 必须提供 --commit-id 参数"
    exit 1
fi

echo "=========================================="
echo "JaCoCo 覆盖率扫描开始"
echo "=========================================="
echo "仓库 URL: $REPO_URL"
echo "提交 ID: $COMMIT_ID"
echo "分支: $BRANCH_NAME"
echo "项目路径: $PROJECT_PATH"
echo "报告路径: $REPORTS_PATH"
echo "=========================================="

# 创建必要的目录
mkdir -p "$REPORTS_PATH"

# 检查是否已存在本地仓库（支持增量更新）
if [[ -d "$PROJECT_PATH/.git" ]]; then
    echo "发现已存在的仓库，使用增量更新..."
    cd "$PROJECT_PATH"

    # 获取最新的远程信息
    echo "获取远程更新..."
    if ! git fetch origin; then
        echo "警告: 获取远程更新失败，尝试重新克隆..."
        cd /app
        rm -rf "$PROJECT_PATH"
        mkdir -p "$PROJECT_PATH"
        if ! git clone "$REPO_URL" "$PROJECT_PATH"; then
            echo "错误: 克隆仓库失败"
            exit 1
        fi
        cd "$PROJECT_PATH"
    fi

    # 切换到指定的提交或分支
    echo "切换到提交/分支: $COMMIT_ID"
    if ! git checkout "$COMMIT_ID"; then
        echo "错误: 切换到提交 $COMMIT_ID 失败"
        exit 1
    fi

    # 如果是分支，拉取最新代码
    if git show-ref --verify --quiet refs/heads/"$COMMIT_ID" 2>/dev/null || git show-ref --verify --quiet refs/remotes/origin/"$COMMIT_ID" 2>/dev/null; then
        echo "拉取分支 $COMMIT_ID 的最新代码..."
        if ! git pull origin "$COMMIT_ID"; then
            echo "警告: 拉取最新代码失败，使用当前代码"
        fi
    fi
else
    echo "首次克隆仓库: $REPO_URL"
    mkdir -p "$PROJECT_PATH"
    if ! git clone "$REPO_URL" "$PROJECT_PATH"; then
        echo "错误: 克隆仓库失败"
        exit 1
    fi

    cd "$PROJECT_PATH"

    # 切换到指定的提交或分支
    echo "切换到提交/分支: $COMMIT_ID"
    if ! git checkout "$COMMIT_ID"; then
        echo "警告: 无法切换到指定提交，使用当前分支"
    fi
fi

# 检查是否为 Maven 项目
if [[ ! -f "pom.xml" ]]; then
    echo "错误: 未找到 pom.xml 文件，不是 Maven 项目"
    exit 1
fi

echo "✓ 找到 Maven 项目"

# 备份原始 pom.xml
echo "备份原始 pom.xml..."
cp pom.xml pom.xml.backup

# 生成增强的 pom.xml
echo "生成增强的 pom.xml..."
/app/scripts/generate-enhanced-pom.sh "$PROJECT_PATH/pom.xml" "$CONFIG_PATH/jacoco-pom-overlay.xml" "$PROJECT_PATH/pom-jacoco.xml"

# 使用增强的 pom.xml 运行测试和生成报告
echo "运行 Maven 测试和 JaCoCo 报告..."
if mvn -f pom-jacoco.xml clean test jacoco:report -Dmaven.test.failure.ignore=true; then
    echo "✓ Maven 测试和 JaCoCo 报告生成成功"
else
    echo "警告: Maven 执行可能有问题，但继续处理报告"
fi

# 检查并复制报告文件
echo "检查生成的报告..."
JACOCO_XML_PATH="$PROJECT_PATH/target/site/jacoco/jacoco.xml"
JACOCO_HTML_DIR="$PROJECT_PATH/target/site/jacoco"
JACOCO_EXEC_PATH="$PROJECT_PATH/target/jacoco/jacoco.exec"

if [[ -f "$JACOCO_XML_PATH" ]]; then
    echo "✓ 找到 JaCoCo XML 报告"
    cp "$JACOCO_XML_PATH" "$REPORTS_PATH/jacoco.xml"
else
    echo "✗ 未找到 JaCoCo XML 报告"
    exit 1
fi

if [[ -d "$JACOCO_HTML_DIR" ]]; then
    echo "✓ 找到 JaCoCo HTML 报告"
    cp -r "$JACOCO_HTML_DIR" "$REPORTS_PATH/html"
else
    echo "✗ 未找到 JaCoCo HTML 报告"
fi

if [[ -f "$JACOCO_EXEC_PATH" ]]; then
    echo "✓ 找到 JaCoCo 执行数据"
    cp "$JACOCO_EXEC_PATH" "$REPORTS_PATH/jacoco.exec"
fi

# 生成报告摘要
echo "生成报告摘要..."
/app/scripts/generate-summary.sh "$REPORTS_PATH/jacoco.xml" "$REPORTS_PATH/summary.json"

# 恢复原始 pom.xml
echo "恢复原始 pom.xml..."
mv pom.xml.backup pom.xml

echo "=========================================="
echo "JaCoCo 覆盖率扫描完成"
echo "=========================================="
echo "报告文件:"
echo "  - XML 报告: $REPORTS_PATH/jacoco.xml"
echo "  - HTML 报告: $REPORTS_PATH/html/"
echo "  - 摘要: $REPORTS_PATH/summary.json"

if [[ -f "$REPORTS_PATH/summary.json" ]]; then
    echo "=========================================="
    echo "覆盖率摘要:"
    cat "$REPORTS_PATH/summary.json"
    echo "=========================================="
fi

echo "扫描成功完成!"
