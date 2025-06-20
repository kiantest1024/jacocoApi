#!/usr/bin/env python3
"""
JaCoCo 覆盖率解析脚本
"""

import sys
import xml.etree.ElementTree as ET
from datetime import datetime

def parse_jacoco_xml(xml_file):
    """解析JaCoCo XML报告"""
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 解析JaCoCo XML: {xml_file}")
        
        tree = ET.parse(xml_file)
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
        counter_elements = root.findall(".//counter")
        print(f"找到 {len(counter_elements)} 个counter元素")
        
        for counter in counter_elements:
            counter_type = counter.get("type")
            missed = int(counter.get("missed", 0))
            covered = int(counter.get("covered", 0))
            
            if counter_type in counters:
                counters[counter_type]["missed"] += missed
                counters[counter_type]["covered"] += covered
                print(f"  {counter_type}: missed={missed}, covered={covered}")
        
        # 计算覆盖率
        def calculate_coverage(counter_data):
            total = counter_data["missed"] + counter_data["covered"]
            return (counter_data["covered"] / total * 100) if total > 0 else 0
        
        # 显示结果
        print("\n" + "="*50)
        print("JaCoCo 覆盖率报告")
        print("="*50)
        
        for counter_type, data in counters.items():
            coverage = calculate_coverage(data)
            total = data["missed"] + data["covered"]
            covered = data["covered"]
            
            print(f"{counter_type:12}: {covered:6}/{total:6} ({coverage:6.2f}%)")
        
        print("="*50)
        
        # 重点显示行覆盖率
        line_coverage = calculate_coverage(counters["LINE"])
        branch_coverage = calculate_coverage(counters["BRANCH"])
        
        print(f"\n🎯 关键指标:")
        print(f"   行覆盖率: {line_coverage:.2f}%")
        print(f"   分支覆盖率: {branch_coverage:.2f}%")
        
        if line_coverage == 0:
            print("\n⚠️  覆盖率为0%的可能原因:")
            print("   1. 项目没有测试代码")
            print("   2. 测试没有执行成功")
            print("   3. JaCoCo代理没有正确附加")
            print("   4. 测试和主代码路径不匹配")
        else:
            print(f"\n✅ 检测到有效覆盖率: {line_coverage:.2f}%")
        
        return {
            "instruction_coverage": calculate_coverage(counters["INSTRUCTION"]),
            "branch_coverage": calculate_coverage(counters["BRANCH"]),
            "line_coverage": calculate_coverage(counters["LINE"]),
            "complexity_coverage": calculate_coverage(counters["COMPLEXITY"]),
            "method_coverage": calculate_coverage(counters["METHOD"]),
            "class_coverage": calculate_coverage(counters["CLASS"]),
            "counters": counters
        }
        
    except ET.ParseError as e:
        print(f"❌ XML解析错误: {e}")
        return None
    except FileNotFoundError:
        print(f"❌ 文件不存在: {xml_file}")
        return None
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return None

def analyze_project_structure():
    """分析项目结构"""
    import os
    
    print(f"\n📁 项目结构分析:")
    
    # 检查源代码
    src_main = "src/main/java"
    src_test = "src/test/java"
    
    if os.path.exists(src_main):
        java_files = []
        for root, dirs, files in os.walk(src_main):
            for file in files:
                if file.endswith('.java'):
                    java_files.append(os.path.join(root, file))
        print(f"   主代码文件: {len(java_files)} 个")
        if java_files:
            print(f"   示例: {java_files[0]}")
    else:
        print(f"   ❌ 主代码目录不存在: {src_main}")
    
    if os.path.exists(src_test):
        test_files = []
        for root, dirs, files in os.walk(src_test):
            for file in files:
                if file.endswith('.java'):
                    test_files.append(os.path.join(root, file))
        print(f"   测试代码文件: {len(test_files)} 个")
        if test_files:
            print(f"   示例: {test_files[0]}")
    else:
        print(f"   ❌ 测试代码目录不存在: {src_test}")
    
    # 检查target目录
    target_dir = "target"
    if os.path.exists(target_dir):
        print(f"   ✅ target目录存在")
        
        # 查找所有jacoco相关文件
        jacoco_files = []
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if 'jacoco' in file.lower():
                    jacoco_files.append(os.path.join(root, file))
        
        if jacoco_files:
            print(f"   JaCoCo相关文件: {len(jacoco_files)} 个")
            for f in jacoco_files[:5]:  # 只显示前5个
                print(f"     - {f}")
        else:
            print(f"   ❌ 未找到JaCoCo相关文件")
    else:
        print(f"   ❌ target目录不存在")

def main():
    if len(sys.argv) != 2:
        print("用法: python3 parse-coverage.py <jacoco.xml>")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    
    # 分析项目结构
    analyze_project_structure()
    
    # 解析覆盖率
    result = parse_jacoco_xml(xml_file)
    
    if result is None:
        print("❌ 覆盖率解析失败")
        sys.exit(1)
    
    print(f"\n✅ 覆盖率解析完成")

if __name__ == "__main__":
    main()
