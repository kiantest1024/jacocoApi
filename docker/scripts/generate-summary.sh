#!/bin/bash

# 生成 JaCoCo 报告摘要脚本
# 从 JaCoCo XML 报告中提取关键信息并生成 JSON 摘要

set -e

JACOCO_XML="$1"
OUTPUT_JSON="$2"

if [[ -z "$JACOCO_XML" || -z "$OUTPUT_JSON" ]]; then
    echo "用法: $0 <jacoco.xml> <output.json>"
    exit 1
fi

if [[ ! -f "$JACOCO_XML" ]]; then
    echo "错误: JaCoCo XML 文件不存在: $JACOCO_XML"
    exit 1
fi

echo "生成 JaCoCo 报告摘要..."
echo "输入文件: $JACOCO_XML"
echo "输出文件: $OUTPUT_JSON"

# 创建临时文件
TEMP_DIR=$(mktemp -d)
TEMP_XML="$TEMP_DIR/jacoco.xml"
cp "$JACOCO_XML" "$TEMP_XML"

# 提取总体覆盖率信息
echo "提取覆盖率信息..."

# 初始化变量
TOTAL_LINES=0
COVERED_LINES=0
TOTAL_BRANCHES=0
COVERED_BRANCHES=0
TOTAL_INSTRUCTIONS=0
COVERED_INSTRUCTIONS=0
TOTAL_METHODS=0
COVERED_METHODS=0
TOTAL_CLASSES=0
COVERED_CLASSES=0

# 提取计数器信息
if command -v xmlstarlet >/dev/null 2>&1; then
    # 使用 xmlstarlet 提取信息
    echo "使用 xmlstarlet 解析 XML..."
    
    # 提取总体计数器
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            TYPE=$(echo "$line" | cut -d'|' -f1)
            MISSED=$(echo "$line" | cut -d'|' -f2)
            COVERED=$(echo "$line" | cut -d'|' -f3)
            
            case "$TYPE" in
                "LINE")
                    TOTAL_LINES=$((MISSED + COVERED))
                    COVERED_LINES=$COVERED
                    ;;
                "BRANCH")
                    TOTAL_BRANCHES=$((MISSED + COVERED))
                    COVERED_BRANCHES=$COVERED
                    ;;
                "INSTRUCTION")
                    TOTAL_INSTRUCTIONS=$((MISSED + COVERED))
                    COVERED_INSTRUCTIONS=$COVERED
                    ;;
                "METHOD")
                    TOTAL_METHODS=$((MISSED + COVERED))
                    COVERED_METHODS=$COVERED
                    ;;
                "CLASS")
                    TOTAL_CLASSES=$((MISSED + COVERED))
                    COVERED_CLASSES=$COVERED
                    ;;
            esac
        fi
    done < <(xmlstarlet sel -t -m "//report/counter" -v "@type" -o "|" -v "@missed" -o "|" -v "@covered" -n "$TEMP_XML" 2>/dev/null || echo "")
    
    # 如果没有找到报告级别的计数器，尝试汇总包级别的
    if [[ $TOTAL_LINES -eq 0 ]]; then
        echo "汇总包级别的覆盖率信息..."
        while IFS= read -r line; do
            if [[ -n "$line" ]]; then
                TYPE=$(echo "$line" | cut -d'|' -f1)
                MISSED=$(echo "$line" | cut -d'|' -f2)
                COVERED=$(echo "$line" | cut -d'|' -f3)
                
                case "$TYPE" in
                    "LINE")
                        TOTAL_LINES=$((TOTAL_LINES + MISSED + COVERED))
                        COVERED_LINES=$((COVERED_LINES + COVERED))
                        ;;
                    "BRANCH")
                        TOTAL_BRANCHES=$((TOTAL_BRANCHES + MISSED + COVERED))
                        COVERED_BRANCHES=$((COVERED_BRANCHES + COVERED))
                        ;;
                    "INSTRUCTION")
                        TOTAL_INSTRUCTIONS=$((TOTAL_INSTRUCTIONS + MISSED + COVERED))
                        COVERED_INSTRUCTIONS=$((COVERED_INSTRUCTIONS + COVERED))
                        ;;
                    "METHOD")
                        TOTAL_METHODS=$((TOTAL_METHODS + MISSED + COVERED))
                        COVERED_METHODS=$((COVERED_METHODS + COVERED))
                        ;;
                    "CLASS")
                        TOTAL_CLASSES=$((TOTAL_CLASSES + MISSED + COVERED))
                        COVERED_CLASSES=$((COVERED_CLASSES + COVERED))
                        ;;
                esac
            fi
        done < <(xmlstarlet sel -t -m "//package/counter" -v "@type" -o "|" -v "@missed" -o "|" -v "@covered" -n "$TEMP_XML" 2>/dev/null || echo "")
    fi
else
    # 使用 grep 和 sed 作为备选方案
    echo "使用 grep/sed 解析 XML..."
    
    # 提取行覆盖率
    LINE_COUNTER=$(grep 'counter type="LINE"' "$TEMP_XML" | head -1 || echo "")
    if [[ -n "$LINE_COUNTER" ]]; then
        TOTAL_LINES=$(echo "$LINE_COUNTER" | sed -n 's/.*missed="\([0-9]*\)".*/\1/p')
        COVERED_LINES=$(echo "$LINE_COUNTER" | sed -n 's/.*covered="\([0-9]*\)".*/\1/p')
        TOTAL_LINES=$((TOTAL_LINES + COVERED_LINES))
    fi
    
    # 提取分支覆盖率
    BRANCH_COUNTER=$(grep 'counter type="BRANCH"' "$TEMP_XML" | head -1 || echo "")
    if [[ -n "$BRANCH_COUNTER" ]]; then
        MISSED_BRANCHES=$(echo "$BRANCH_COUNTER" | sed -n 's/.*missed="\([0-9]*\)".*/\1/p')
        COVERED_BRANCHES=$(echo "$BRANCH_COUNTER" | sed -n 's/.*covered="\([0-9]*\)".*/\1/p')
        TOTAL_BRANCHES=$((MISSED_BRANCHES + COVERED_BRANCHES))
    fi
fi

# 计算百分比
LINE_COVERAGE=0
BRANCH_COVERAGE=0
INSTRUCTION_COVERAGE=0
METHOD_COVERAGE=0
CLASS_COVERAGE=0

if [[ $TOTAL_LINES -gt 0 ]]; then
    LINE_COVERAGE=$(echo "scale=2; $COVERED_LINES * 100 / $TOTAL_LINES" | bc -l 2>/dev/null || echo "0")
fi

if [[ $TOTAL_BRANCHES -gt 0 ]]; then
    BRANCH_COVERAGE=$(echo "scale=2; $COVERED_BRANCHES * 100 / $TOTAL_BRANCHES" | bc -l 2>/dev/null || echo "0")
fi

if [[ $TOTAL_INSTRUCTIONS -gt 0 ]]; then
    INSTRUCTION_COVERAGE=$(echo "scale=2; $COVERED_INSTRUCTIONS * 100 / $TOTAL_INSTRUCTIONS" | bc -l 2>/dev/null || echo "0")
fi

if [[ $TOTAL_METHODS -gt 0 ]]; then
    METHOD_COVERAGE=$(echo "scale=2; $COVERED_METHODS * 100 / $TOTAL_METHODS" | bc -l 2>/dev/null || echo "0")
fi

if [[ $TOTAL_CLASSES -gt 0 ]]; then
    CLASS_COVERAGE=$(echo "scale=2; $COVERED_CLASSES * 100 / $TOTAL_CLASSES" | bc -l 2>/dev/null || echo "0")
fi

# 生成 JSON 摘要
echo "生成 JSON 摘要..."

cat > "$OUTPUT_JSON" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "coverage": {
    "line": {
      "percentage": $LINE_COVERAGE,
      "covered": $COVERED_LINES,
      "total": $TOTAL_LINES
    },
    "branch": {
      "percentage": $BRANCH_COVERAGE,
      "covered": $COVERED_BRANCHES,
      "total": $TOTAL_BRANCHES
    },
    "instruction": {
      "percentage": $INSTRUCTION_COVERAGE,
      "covered": $COVERED_INSTRUCTIONS,
      "total": $TOTAL_INSTRUCTIONS
    },
    "method": {
      "percentage": $METHOD_COVERAGE,
      "covered": $COVERED_METHODS,
      "total": $TOTAL_METHODS
    },
    "class": {
      "percentage": $CLASS_COVERAGE,
      "covered": $COVERED_CLASSES,
      "total": $TOTAL_CLASSES
    }
  },
  "summary": {
    "overall_coverage": $LINE_COVERAGE,
    "status": "$(if (( $(echo "$LINE_COVERAGE >= 50" | bc -l 2>/dev/null || echo "0") )); then echo "good"; elif (( $(echo "$LINE_COVERAGE >= 30" | bc -l 2>/dev/null || echo "0") )); then echo "fair"; else echo "poor"; fi)"
  }
}
EOF

# 清理临时文件
rm -rf "$TEMP_DIR"

echo "✓ JaCoCo 报告摘要生成完成: $OUTPUT_JSON"
echo "覆盖率摘要:"
echo "  行覆盖率: ${LINE_COVERAGE}% (${COVERED_LINES}/${TOTAL_LINES})"
echo "  分支覆盖率: ${BRANCH_COVERAGE}% (${COVERED_BRANCHES}/${TOTAL_BRANCHES})"
