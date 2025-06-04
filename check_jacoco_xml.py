#!/usr/bin/env python3
"""
检查JaCoCo XML报告内容
"""

import xml.etree.ElementTree as ET

def check_jacoco_xml(xml_path):
    """检查JaCoCo XML报告"""
    try:
        print(f"🔍 检查JaCoCo XML报告: {xml_path}")
        
        # 读取XML文件
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        print(f"📄 根元素: {root.tag}")
        print(f"📄 属性: {root.attrib}")
        
        # 查找覆盖率数据
        counters = root.findall('.//counter')
        print(f"\n📊 找到 {len(counters)} 个覆盖率计数器:")
        
        total_coverage = {}
        
        for counter in counters:
            counter_type = counter.get('type')
            missed = int(counter.get('missed', 0))
            covered = int(counter.get('covered', 0))
            total = missed + covered
            
            if total > 0:
                coverage_percent = (covered / total) * 100
                total_coverage[counter_type] = {
                    'covered': covered,
                    'missed': missed,
                    'total': total,
                    'percentage': coverage_percent
                }
                
                print(f"  📈 {counter_type}: {covered}/{total} ({coverage_percent:.2f}%)")
            else:
                print(f"  📈 {counter_type}: 0/0 (0%)")
        
        # 查找包信息
        packages = root.findall('.//package')
        print(f"\n📦 找到 {len(packages)} 个包:")
        for package in packages:
            package_name = package.get('name', 'default')
            print(f"  📁 {package_name}")
            
            # 查找类信息
            classes = package.findall('.//class')
            print(f"    📄 {len(classes)} 个类")
            for cls in classes:
                class_name = cls.get('name', 'unknown')
                print(f"      🔸 {class_name}")
        
        # 显示总体覆盖率
        if total_coverage:
            print(f"\n📊 总体覆盖率摘要:")
            for coverage_type, data in total_coverage.items():
                print(f"  {coverage_type}: {data['percentage']:.2f}% ({data['covered']}/{data['total']})")
        
        return total_coverage
        
    except Exception as e:
        print(f"❌ 检查XML失败: {e}")
        return None

def test_with_temp_file():
    """使用临时目录中的文件测试"""
    import os
    
    # 从调试输出中的临时目录
    temp_dir = "/tmp/debug_jacoco_detailed_gq0koty9"
    xml_path = os.path.join(temp_dir, "repo", "target", "site", "jacoco", "jacoco.xml")
    
    if os.path.exists(xml_path):
        print("✅ 找到临时目录中的JaCoCo XML文件")
        coverage_data = check_jacoco_xml(xml_path)
        
        if coverage_data:
            print(f"\n🎉 成功解析覆盖率数据!")
            return True
        else:
            print(f"\n❌ 解析覆盖率数据失败")
            return False
    else:
        print(f"❌ 临时目录中的XML文件不存在: {xml_path}")
        print("请重新运行 debug_jacoco_detailed.py 并保持临时目录")
        return False

if __name__ == "__main__":
    test_with_temp_file()
