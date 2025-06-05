#!/usr/bin/env python3

import subprocess
import tempfile
import os
import time

def test_docker_coverage():
    print("🧪 测试Docker JaCoCo覆盖率修复...")
    
    # 重建Docker镜像
    print("🔨 重建Docker镜像...")
    try:
        subprocess.run(["docker", "rmi", "jacoco-scanner:latest"], 
                      capture_output=True, check=False)
        
        result = subprocess.run(["docker", "build", "-t", "jacoco-scanner:latest", "."], 
                               capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print("❌ Docker镜像构建失败")
            print(f"错误: {result.stderr}")
            return False
        
        print("✅ Docker镜像构建成功")
        
    except Exception as e:
        print(f"❌ Docker构建异常: {e}")
        return False
    
    # 测试Docker扫描
    print("🚀 测试Docker扫描...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 使用临时目录: {temp_dir}")
        
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
            result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=300)
            
            print(f"📊 Docker扫描结果:")
            print(f"返回码: {result.returncode}")
            print(f"输出: {result.stdout}")
            if result.stderr:
                print(f"错误: {result.stderr}")
            
            # 检查生成的报告
            jacoco_xml = os.path.join(temp_dir, "jacoco.xml")
            if os.path.exists(jacoco_xml):
                print("✅ 找到JaCoCo XML报告")
                
                # 读取并分析XML内容
                with open(jacoco_xml, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                print(f"📄 XML文件大小: {len(xml_content)} 字符")
                print("📄 XML内容预览:")
                print(xml_content[:500] + "..." if len(xml_content) > 500 else xml_content)
                
                # 检查是否包含实际的覆盖率数据
                if 'covered="0"' in xml_content and 'missed="0"' in xml_content:
                    print("⚠️ 警告: 报告显示覆盖率为0，可能存在问题")
                    return False
                elif 'covered=' in xml_content:
                    print("✅ 报告包含覆盖率数据")
                    return True
                else:
                    print("❌ 报告格式异常")
                    return False
            else:
                print("❌ 未找到JaCoCo XML报告")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Docker扫描超时")
            return False
        except Exception as e:
            print(f"❌ Docker扫描异常: {e}")
            return False

def main():
    print("🔧 JaCoCo覆盖率问题修复测试")
    print("=" * 50)
    
    if test_docker_coverage():
        print("\n🎉 覆盖率修复测试通过！")
    else:
        print("\n❌ 覆盖率修复测试失败")
        print("建议检查:")
        print("1. 测试项目是否有实际的测试用例")
        print("2. Maven配置是否正确")
        print("3. JaCoCo插件配置是否正确")

if __name__ == "__main__":
    main()
