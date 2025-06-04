#!/usr/bin/env python3
"""
分析Java项目覆盖率为0%的原因
"""

import os
import subprocess
import tempfile
import shutil

def analyze_java_project():
    """分析Java项目"""
    print("🔍 分析Java项目覆盖率问题")
    print("=" * 60)
    
    # 克隆项目到临时目录
    temp_dir = tempfile.mkdtemp()
    repo_dir = os.path.join(temp_dir, "repo")
    
    try:
        print("📥 克隆Java项目...")
        subprocess.run([
            "git", "clone", 
            "http://172.16.1.30/kian/backend-lotto-game.git",
            repo_dir
        ], check=True, capture_output=True)
        
        print("✅ 项目克隆成功")
        
        # 分析项目结构
        analyze_project_structure(repo_dir)
        
        # 分析pom.xml
        analyze_pom_xml(repo_dir)
        
        # 分析测试代码
        analyze_test_code(repo_dir)
        
        # 尝试本地Maven测试
        test_maven_locally(repo_dir)
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def analyze_project_structure(repo_dir):
    """分析项目结构"""
    print("\n📁 项目结构分析:")
    
    # 检查主代码
    src_main_java = os.path.join(repo_dir, "src", "main", "java")
    if os.path.exists(src_main_java):
        main_files = []
        for root, _, files in os.walk(src_main_java):
            for file in files:
                if file.endswith('.java'):
                    rel_path = os.path.relpath(os.path.join(root, file), src_main_java)
                    main_files.append(rel_path)
        
        print(f"✅ 主代码目录存在: {len(main_files)} 个Java文件")
        if main_files:
            print(f"  示例: {main_files[:3]}")
    else:
        print("❌ 主代码目录不存在")
    
    # 检查测试代码
    src_test_java = os.path.join(repo_dir, "src", "test", "java")
    if os.path.exists(src_test_java):
        test_files = []
        for root, _, files in os.walk(src_test_java):
            for file in files:
                if file.endswith('.java'):
                    rel_path = os.path.relpath(os.path.join(root, file), src_test_java)
                    test_files.append(rel_path)
        
        print(f"✅ 测试代码目录存在: {len(test_files)} 个Java文件")
        if test_files:
            print(f"  示例: {test_files[:3]}")
            
            # 检查测试文件命名
            proper_test_files = [f for f in test_files if 
                               f.endswith('Test.java') or 
                               f.startswith('Test') or 
                               'Test' in f]
            print(f"  符合测试命名规范的文件: {len(proper_test_files)}")
    else:
        print("❌ 测试代码目录不存在")

def analyze_pom_xml(repo_dir):
    """分析pom.xml"""
    print("\n📄 pom.xml分析:")
    
    pom_path = os.path.join(repo_dir, "pom.xml")
    if not os.path.exists(pom_path):
        print("❌ pom.xml不存在")
        return
    
    with open(pom_path, 'r', encoding='utf-8') as f:
        pom_content = f.read()
    
    # 检查父POM
    if '<parent>' in pom_content:
        print("⚠️ 项目有父POM依赖")
        # 提取父POM信息
        import re
        parent_match = re.search(r'<parent>.*?<groupId>([^<]+)</groupId>.*?<artifactId>([^<]+)</artifactId>.*?<version>([^<]+)</version>.*?</parent>', pom_content, re.DOTALL)
        if parent_match:
            print(f"  父POM: {parent_match.group(1)}:{parent_match.group(2)}:{parent_match.group(3)}")
    
    # 检查JaCoCo插件
    if 'jacoco' in pom_content.lower():
        print("✅ 项目已配置JaCoCo插件")
    else:
        print("⚠️ 项目未配置JaCoCo插件")
    
    # 检查Surefire插件
    if 'maven-surefire-plugin' in pom_content:
        print("✅ 项目已配置Surefire插件")
    else:
        print("⚠️ 项目未配置Surefire插件")
    
    # 检查JUnit依赖
    if 'junit' in pom_content.lower():
        print("✅ 项目有JUnit依赖")
    else:
        print("⚠️ 项目无JUnit依赖")

def analyze_test_code(repo_dir):
    """分析测试代码"""
    print("\n🧪 测试代码分析:")
    
    src_test_java = os.path.join(repo_dir, "src", "test", "java")
    if not os.path.exists(src_test_java):
        print("❌ 无测试代码")
        return
    
    test_methods_count = 0
    test_files_with_tests = 0
    
    for root, _, files in os.walk(src_test_java):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 检查@Test注解
                    test_methods = content.count('@Test')
                    if test_methods > 0:
                        test_files_with_tests += 1
                        test_methods_count += test_methods
                        print(f"  {file}: {test_methods} 个测试方法")
                except Exception as e:
                    print(f"  ⚠️ 读取{file}失败: {e}")
    
    print(f"📊 测试统计:")
    print(f"  有测试方法的文件: {test_files_with_tests}")
    print(f"  总测试方法数: {test_methods_count}")

def test_maven_locally(repo_dir):
    """本地测试Maven"""
    print("\n🔧 本地Maven测试:")
    
    try:
        # 检查Maven版本
        result = subprocess.run(["mvn", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Maven可用")
            print(f"  版本: {result.stdout.split()[2]}")
        else:
            print("❌ Maven不可用")
            return
    except Exception as e:
        print(f"❌ Maven检查失败: {e}")
        return
    
    # 尝试编译
    print("\n🔨 尝试编译...")
    try:
        result = subprocess.run([
            "mvn", "clean", "compile", "test-compile",
            "-Dmaven.test.skip=true"
        ], cwd=repo_dir, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ 编译成功")
        else:
            print("❌ 编译失败")
            print("错误信息:")
            for line in result.stdout.split('\n')[-10:]:
                if line.strip():
                    print(f"  {line}")
    except Exception as e:
        print(f"❌ 编译测试失败: {e}")
    
    # 尝试运行测试
    print("\n🧪 尝试运行测试...")
    try:
        result = subprocess.run([
            "mvn", "test", "-Dmaven.test.failure.ignore=true"
        ], cwd=repo_dir, capture_output=True, text=True, timeout=300)
        
        output = result.stdout
        if "Tests run:" in output:
            print("✅ 测试已执行")
            # 提取测试结果
            for line in output.split('\n'):
                if "Tests run:" in line:
                    print(f"  {line.strip()}")
        else:
            print("⚠️ 未检测到测试执行")
            
        if "BUILD SUCCESS" in output:
            print("✅ Maven构建成功")
        elif "BUILD FAILURE" in output:
            print("❌ Maven构建失败")
            
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")

def provide_solutions():
    """提供解决方案"""
    print("\n💡 Java项目0%覆盖率解决方案")
    print("=" * 60)
    
    print("1. **确保测试正确命名**:")
    print("   - 测试类以Test结尾（如UserServiceTest.java）")
    print("   - 测试方法有@Test注解")
    print("   - 测试类在src/test/java目录下")
    
    print("\n2. **确保测试实际调用主代码**:")
    print("   - 测试方法中要实例化和调用主代码类")
    print("   - 检查包路径是否正确")
    print("   - 确保测试覆盖了主要的业务逻辑")
    
    print("\n3. **优化JaCoCo配置**:")
    print("   - 使用prepare-agent目标")
    print("   - 确保Surefire插件正确配置")
    print("   - 检查JaCoCo代理是否正确附加")
    
    print("\n4. **解决父POM问题**:")
    print("   - 系统会自动创建独立pom.xml")
    print("   - 确保所有必要的依赖都包含在内")
    print("   - 检查Java版本兼容性")

def main():
    """主函数"""
    analyze_java_project()
    provide_solutions()
    
    print("\n🎯 建议:")
    print("1. 运行此分析脚本查看项目详情")
    print("2. 检查测试代码是否正确")
    print("3. 使用增强的JaCoCo配置重新扫描")
    print("4. 如果仍有问题，可以手动调试Maven命令")

if __name__ == "__main__":
    main()
