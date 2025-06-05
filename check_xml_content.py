#!/usr/bin/env python3

import subprocess
import tempfile
import os
import xml.etree.ElementTree as ET

def check_docker_xml():
    print("🔍 检查Docker生成的JaCoCo XML内容...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 临时目录: {temp_dir}")
        
        # 运行Docker扫描
        print("🚀 运行Docker扫描...")
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{temp_dir}:/app/reports",
            "jacoco-scanner:latest",
            "--repo-url", "http://172.16.1.30/kian/jacocotest.git",
            "--commit-id", "5ea76b4989a17153eade57d7d55609ebad7fdd9e",
            "--branch", "main",
            "--service-name", "jacocotest"
        ]
        
        try:
            result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=180)
            print(f"Docker返回码: {result.returncode}")
            print(f"Docker输出: {result.stdout}")
            if result.stderr:
                print(f"Docker错误: {result.stderr}")
        except Exception as e:
            print(f"❌ Docker执行失败: {e}")
            return False
        
        # 检查生成的XML文件
        xml_file = os.path.join(temp_dir, "jacoco.xml")
        if os.path.exists(xml_file):
            print(f"✅ 找到XML文件: {xml_file}")
            
            # 读取XML内容
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            print(f"📄 XML文件大小: {len(xml_content)} 字符")
            print("📄 XML完整内容:")
            print("=" * 50)
            print(xml_content)
            print("=" * 50)
            
            # 尝试解析XML
            try:
                root = ET.fromstring(xml_content)
                print(f"✅ XML解析成功")
                print(f"根元素: {root.tag}")
                print(f"根元素属性: {root.attrib}")
                
                # 查找所有counter元素
                counters = root.findall(".//counter")
                print(f"找到 {len(counters)} 个counter元素:")
                
                for i, counter in enumerate(counters):
                    counter_type = counter.get("type")
                    missed = counter.get("missed", "0")
                    covered = counter.get("covered", "0")
                    print(f"  Counter {i+1}: type={counter_type}, missed={missed}, covered={covered}")
                
                # 计算总覆盖率
                total_instructions = 0
                covered_instructions = 0
                
                for counter in counters:
                    if counter.get("type") == "INSTRUCTION":
                        missed = int(counter.get("missed", 0))
                        covered = int(counter.get("covered", 0))
                        total_instructions += missed + covered
                        covered_instructions += covered
                
                if total_instructions > 0:
                    coverage = (covered_instructions / total_instructions) * 100
                    print(f"✅ 计算得到的指令覆盖率: {coverage:.2f}%")
                    return True
                else:
                    print("❌ 没有指令覆盖率数据")
                    return False
                    
            except Exception as e:
                print(f"❌ XML解析失败: {e}")
                return False
        else:
            print("❌ 未找到XML文件")
            return False

def main():
    print("🔧 检查Docker JaCoCo XML内容")
    print("=" * 50)
    
    if check_docker_xml():
        print("\n🎉 XML内容检查通过！")
    else:
        print("\n❌ XML内容检查失败")

if __name__ == "__main__":
    main()
