#!/bin/bash

# 生成JaCoCo覆盖率摘要
set -e

REPORTS_DIR="$1"

if [[ -z "$REPORTS_DIR" ]]; then
    echo "用法: $0 <reports_dir>"
    exit 1
fi

JACOCO_XML="$REPORTS_DIR/jacoco.xml"
SUMMARY_JSON="$REPORTS_DIR/summary.json"

if [[ ! -f "$JACOCO_XML" ]]; then
    echo "警告: 未找到JaCoCo XML报告: $JACOCO_XML"
    # 创建空的摘要
    cat > "$SUMMARY_JSON" << 'EOF'
{
    "instruction_coverage": 0,
    "branch_coverage": 0,
    "line_coverage": 0,
    "complexity_coverage": 0,
    "method_coverage": 0,
    "class_coverage": 0,
    "instructions_covered": 0,
    "instructions_total": 0,
    "branches_covered": 0,
    "branches_total": 0,
    "lines_covered": 0,
    "lines_total": 0,
    "complexity_covered": 0,
    "complexity_total": 0,
    "methods_covered": 0,
    "methods_total": 0,
    "classes_covered": 0,
    "classes_total": 0
}
EOF
    exit 0
fi

echo "解析JaCoCo XML报告..."

# 使用Python解析XML并生成JSON摘要
python3 << EOF
import xml.etree.ElementTree as ET
import json

try:
    tree = ET.parse('$JACOCO_XML')
    root = tree.getroot()
    
    # 初始化计数器
    counters = {
        "INSTRUCTION": {"missed": 0, "covered": 0},
        "BRANCH": {"missed": 0, "covered": 0},
        "LINE": {"missed": 0, "covered": 0},
        "COMPLEXITY": {"missed": 0, "covered": 0},
        "METHOD": {"missed": 0, "covered": 0},
        "CLASS": {"missed": 0, "covered": 0}
    }
    
    # 解析所有counter元素
    for counter in root.findall(".//counter"):
        counter_type = counter.get("type")
        missed = int(counter.get("missed", 0))
        covered = int(counter.get("covered", 0))
        
        if counter_type in counters:
            counters[counter_type]["missed"] += missed
            counters[counter_type]["covered"] += covered
    
    # 计算覆盖率
    def calculate_coverage(counter_data):
        total = counter_data["missed"] + counter_data["covered"]
        return (counter_data["covered"] / total * 100) if total > 0 else 0
    
    summary = {
        "instruction_coverage": round(calculate_coverage(counters["INSTRUCTION"]), 2),
        "branch_coverage": round(calculate_coverage(counters["BRANCH"]), 2),
        "line_coverage": round(calculate_coverage(counters["LINE"]), 2),
        "complexity_coverage": round(calculate_coverage(counters["COMPLEXITY"]), 2),
        "method_coverage": round(calculate_coverage(counters["METHOD"]), 2),
        "class_coverage": round(calculate_coverage(counters["CLASS"]), 2),
        "instructions_covered": counters["INSTRUCTION"]["covered"],
        "instructions_total": counters["INSTRUCTION"]["missed"] + counters["INSTRUCTION"]["covered"],
        "branches_covered": counters["BRANCH"]["covered"],
        "branches_total": counters["BRANCH"]["missed"] + counters["BRANCH"]["covered"],
        "lines_covered": counters["LINE"]["covered"],
        "lines_total": counters["LINE"]["missed"] + counters["LINE"]["covered"],
        "complexity_covered": counters["COMPLEXITY"]["covered"],
        "complexity_total": counters["COMPLEXITY"]["missed"] + counters["COMPLEXITY"]["covered"],
        "methods_covered": counters["METHOD"]["covered"],
        "methods_total": counters["METHOD"]["missed"] + counters["METHOD"]["covered"],
        "classes_covered": counters["CLASS"]["covered"],
        "classes_total": counters["CLASS"]["missed"] + counters["CLASS"]["covered"]
    }
    
    # 写入JSON文件
    with open('$SUMMARY_JSON', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("覆盖率摘要生成完成")
    print(f"行覆盖率: {summary['line_coverage']:.2f}%")
    print(f"分支覆盖率: {summary['branch_coverage']:.2f}%")
    
except Exception as e:
    print(f"解析JaCoCo XML失败: {e}")
    exit(1)
EOF

echo "摘要生成完成: $SUMMARY_JSON"
