#!/usr/bin/env python3

import subprocess
import tempfile
import os

def debug_xml_content():
    print("🔍 调试Docker生成的XML内容...")
    
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
            print("Docker输出:")
            print("=" * 50)
            print(result.stdout)
            print("=" * 50)
            if result.stderr:
                print("Docker错误:")
                print(result.stderr)
        except Exception as e:
            print(f"❌ Docker执行失败: {e}")
            return
        
        # 检查生成的XML文件
        xml_file = os.path.join(temp_dir, "jacoco.xml")
        if os.path.exists(xml_file):
            print(f"✅ 找到XML文件")
            
            # 读取XML内容
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            print(f"📄 XML文件大小: {len(xml_content)} 字符")
            print("📄 XML完整内容:")
            print("=" * 50)
            print(xml_content)
            print("=" * 50)
            
            # 分析XML结构
            if '<report' in xml_content:
                print("✅ XML包含report元素")
            else:
                print("❌ XML不包含report元素")
                
            if '<package' in xml_content:
                print("✅ XML包含package元素")
            else:
                print("❌ XML不包含package元素")
                
            if '<class' in xml_content:
                print("✅ XML包含class元素")
            else:
                print("❌ XML不包含class元素")
                
            if '<counter' in xml_content:
                print("✅ XML包含counter元素")
                counter_count = xml_content.count('<counter')
                print(f"Counter元素数量: {counter_count}")
            else:
                print("❌ XML不包含counter元素")
                
            # 检查是否是空报告
            if 'name="empty"' in xml_content:
                print("⚠️ 这是一个空报告（fallback报告）")
            else:
                print("✅ 这不是空报告")
                
        else:
            print("❌ 未找到XML文件")

def main():
    print("🔧 调试Docker JaCoCo XML内容")
    print("=" * 50)
    
    debug_xml_content()

if __name__ == "__main__":
    main()
