#!/usr/bin/env python3

import subprocess
import tempfile
import os
import shutil

def check_project_structure():
    print("🔍 检查jacocotest项目结构...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 临时目录: {temp_dir}")
        
        # 克隆项目
        print("📥 克隆项目...")
        try:
            result = subprocess.run([
                "git", "clone", 
                "http://172.16.1.30/kian/jacocotest.git",
                os.path.join(temp_dir, "jacocotest")
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                print(f"❌ 克隆失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 克隆异常: {e}")
            return False
        
        project_dir = os.path.join(temp_dir, "jacocotest")
        os.chdir(project_dir)
        
        # 检查项目结构
        print("📂 项目文件结构:")
        for root, dirs, files in os.walk("."):
            level = root.replace(".", "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files:
                if file.endswith(('.java', '.xml', '.properties')):
                    print(f"{subindent}{file}")
        
        # 检查pom.xml
        if os.path.exists("pom.xml"):
            print("\n📄 原始pom.xml内容:")
            with open("pom.xml", "r", encoding="utf-8") as f:
                content = f.read()
                print(content)
        else:
            print("❌ 未找到pom.xml文件")
            return False
        
        # 查找Java源文件
        java_files = []
        test_files = []
        
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(".java"):
                    full_path = os.path.join(root, file)
                    if "/test/" in full_path:
                        test_files.append(full_path)
                    elif "/main/" in full_path:
                        java_files.append(full_path)
        
        print(f"\n💻 源代码文件 ({len(java_files)}):")
        for f in java_files[:10]:
            print(f"  {f}")
        
        print(f"\n🧪 测试文件 ({len(test_files)}):")
        for f in test_files[:10]:
            print(f"  {f}")
        
        # 检查测试文件内容
        if test_files:
            print(f"\n📝 第一个测试文件内容:")
            try:
                with open(test_files[0], "r", encoding="utf-8") as f:
                    content = f.read()
                    print(content[:500] + "..." if len(content) > 500 else content)
            except Exception as e:
                print(f"读取失败: {e}")
        
        # 尝试运行Maven测试
        print("\n🔨 尝试运行Maven测试...")
        try:
            result = subprocess.run([
                "mvn", "clean", "test", 
                "-Dmaven.test.failure.ignore=true",
                "--batch-mode"
            ], capture_output=True, text=True, timeout=120)
            
            print(f"Maven返回码: {result.returncode}")
            print(f"Maven输出: {result.stdout[-1000:]}")  # 最后1000字符
            if result.stderr:
                print(f"Maven错误: {result.stderr[-500:]}")  # 最后500字符
                
        except Exception as e:
            print(f"Maven执行异常: {e}")
        
        # 检查是否生成了测试报告
        print("\n📊 检查生成的文件:")
        for root, dirs, files in os.walk("."):
            for file in files:
                if any(keyword in file.lower() for keyword in ['test', 'jacoco', 'surefire']):
                    print(f"  {os.path.join(root, file)}")
        
        return True

def main():
    print("🔧 JaCoCo项目结构检查")
    print("=" * 50)
    
    check_project_structure()

if __name__ == "__main__":
    main()
