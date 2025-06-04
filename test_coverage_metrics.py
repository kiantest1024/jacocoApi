#!/usr/bin/env python3
"""
JaCoCo覆盖率指标测试脚本
验证所有6项JaCoCo标准覆盖率指标是否正确实现
"""

import json
import tempfile
import os
from jacoco_tasks import parse_jacoco_xml_file

def create_sample_jacoco_xml():
    """创建示例JaCoCo XML报告用于测试"""
    xml_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!DOCTYPE report PUBLIC "-//JACOCO//DTD Report 1.1//EN" "report.dtd">
<report name="jacocoTest">
    <sessioninfo id="test-session" start="1640995200000" dump="1640995260000"/>
    <package name="com/example/demo">
        <class name="com/example/demo/Calculator" sourcefilename="Calculator.java">
            <method name="&lt;init&gt;" desc="()V" line="5">
                <counter type="INSTRUCTION" missed="0" covered="3"/>
                <counter type="BRANCH" missed="0" covered="0"/>
                <counter type="LINE" missed="0" covered="1"/>
                <counter type="COMPLEXITY" missed="0" covered="1"/>
                <counter type="METHOD" missed="0" covered="1"/>
            </method>
            <method name="add" desc="(II)I" line="8">
                <counter type="INSTRUCTION" missed="0" covered="4"/>
                <counter type="BRANCH" missed="0" covered="0"/>
                <counter type="LINE" missed="0" covered="1"/>
                <counter type="COMPLEXITY" missed="0" covered="1"/>
                <counter type="METHOD" missed="0" covered="1"/>
            </method>
            <method name="divide" desc="(II)I" line="12">
                <counter type="INSTRUCTION" missed="8" covered="7"/>
                <counter type="BRANCH" missed="1" covered="1"/>
                <counter type="LINE" missed="2" covered="3"/>
                <counter type="COMPLEXITY" missed="1" covered="1"/>
                <counter type="METHOD" missed="0" covered="1"/>
            </method>
            <counter type="INSTRUCTION" missed="8" covered="14"/>
            <counter type="BRANCH" missed="1" covered="1"/>
            <counter type="LINE" missed="2" covered="5"/>
            <counter type="COMPLEXITY" missed="1" covered="3"/>
            <counter type="METHOD" missed="0" covered="3"/>
            <counter type="CLASS" missed="0" covered="1"/>
        </class>
        <sourcefile name="Calculator.java">
            <line nr="5" mi="0" ci="3" mb="0" cb="0"/>
            <line nr="8" mi="0" ci="4" mb="0" cb="0"/>
            <line nr="12" mi="0" ci="2" mb="0" cb="0"/>
            <line nr="13" mi="0" ci="2" mb="1" cb="1"/>
            <line nr="15" mi="8" ci="0" mb="0" cb="0"/>
            <line nr="16" mi="0" ci="3" mb="0" cb="0"/>
            <counter type="INSTRUCTION" missed="8" covered="14"/>
            <counter type="BRANCH" missed="1" covered="1"/>
            <counter type="LINE" missed="2" covered="5"/>
            <counter type="COMPLEXITY" missed="1" covered="3"/>
            <counter type="METHOD" missed="0" covered="3"/>
            <counter type="CLASS" missed="0" covered="1"/>
        </sourcefile>
        <counter type="INSTRUCTION" missed="8" covered="14"/>
        <counter type="BRANCH" missed="1" covered="1"/>
        <counter type="LINE" missed="2" covered="5"/>
        <counter type="COMPLEXITY" missed="1" covered="3"/>
        <counter type="METHOD" missed="0" covered="3"/>
        <counter type="CLASS" missed="0" covered="1"/>
    </package>
    <counter type="INSTRUCTION" missed="8" covered="14"/>
    <counter type="BRANCH" missed="1" covered="1"/>
    <counter type="LINE" missed="2" covered="5"/>
    <counter type="COMPLEXITY" missed="1" covered="3"/>
    <counter type="METHOD" missed="0" covered="3"/>
    <counter type="CLASS" missed="0" covered="1"/>
</report>'''
    
    # 创建临时XML文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        f.write(xml_content)
        return f.name

def test_jacoco_coverage_metrics():
    """测试JaCoCo覆盖率指标解析"""
    
    print("🧪 JaCoCo覆盖率指标测试")
    print("=" * 60)
    
    # 创建示例XML文件
    xml_file = create_sample_jacoco_xml()
    request_id = "test_coverage_metrics"
    
    try:
        print(f"📄 解析测试XML文件: {xml_file}")
        
        # 解析XML文件
        result = parse_jacoco_xml_file(xml_file, request_id)
        
        print("\n📊 解析结果:")
        print("=" * 40)
        
        # 验证所有6项JaCoCo标准指标
        expected_metrics = [
            "instruction_coverage",
            "branch_coverage", 
            "line_coverage",
            "complexity_coverage",
            "method_coverage",
            "class_coverage"
        ]
        
        print("🎯 覆盖率指标:")
        for metric in expected_metrics:
            if metric in result:
                value = result[metric]
                print(f"  ✅ {metric}: {value}%")
            else:
                print(f"  ❌ {metric}: 缺失")
        
        print("\n📈 详细统计:")
        detail_metrics = [
            ("instructions", "指令"),
            ("branches", "分支"),
            ("lines", "行"),
            ("complexity", "圈复杂度"),
            ("methods", "方法"),
            ("classes", "类")
        ]
        
        for metric_key, metric_name in detail_metrics:
            covered_key = f"{metric_key}_covered"
            total_key = f"{metric_key}_total"
            
            if covered_key in result and total_key in result:
                covered = result[covered_key]
                total = result[total_key]
                print(f"  📊 {metric_name}: {covered}/{total}")
            else:
                print(f"  ❌ {metric_name}: 统计数据缺失")
        
        # 验证计算是否正确
        print("\n🔍 计算验证:")
        
        # 根据XML数据验证计算
        expected_values = {
            "instruction_coverage": 14 / (14 + 8) * 100,  # 63.64%
            "branch_coverage": 1 / (1 + 1) * 100,         # 50.00%
            "line_coverage": 5 / (5 + 2) * 100,           # 71.43%
            "complexity_coverage": 3 / (3 + 1) * 100,     # 75.00%
            "method_coverage": 3 / (3 + 0) * 100,         # 100.00%
            "class_coverage": 1 / (1 + 0) * 100           # 100.00%
        }
        
        all_correct = True
        for metric, expected in expected_values.items():
            if metric in result:
                actual = result[metric]
                if abs(actual - expected) < 0.01:  # 允许小数点误差
                    print(f"  ✅ {metric}: {actual:.2f}% (期望: {expected:.2f}%)")
                else:
                    print(f"  ❌ {metric}: {actual:.2f}% (期望: {expected:.2f}%)")
                    all_correct = False
            else:
                print(f"  ❌ {metric}: 缺失")
                all_correct = False
        
        print("\n" + "=" * 60)
        if all_correct:
            print("🎉 所有JaCoCo覆盖率指标测试通过！")
            print("✅ 指令覆盖率、分支覆盖率、行覆盖率、圈复杂度覆盖率、方法覆盖率、类覆盖率")
            print("✅ 所有6项JaCoCo标准指标均已正确实现")
        else:
            print("❌ 部分指标测试失败，请检查实现")
        
        # 显示完整结果用于调试
        print(f"\n🔧 完整解析结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理临时文件
        try:
            os.unlink(xml_file)
            print(f"\n🧹 清理临时文件: {xml_file}")
        except:
            pass

if __name__ == "__main__":
    test_jacoco_coverage_metrics()
