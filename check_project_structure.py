#!/usr/bin/env python3
"""
检查项目结构并创建示例代码
"""

import os
import subprocess
import tempfile
import shutil

def check_project_structure():
    """检查项目结构"""
    
    repo_url = "http://172.16.1.30/kian/jacocotest.git"
    commit_id = "84d32a75d4832dc26f33678706bc8446da51cda0"
    
    print("🔍 检查项目结构")
    print("=" * 50)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="check_project_")
    repo_dir = os.path.join(temp_dir, "repo")
    
    try:
        # 1. 克隆仓库
        print(f"📥 克隆仓库...")
        clone_cmd = ["git", "clone", repo_url, repo_dir]
        result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ 克隆失败: {result.stderr}")
            return
        
        print("✅ 克隆成功")
        
        # 2. 切换提交
        checkout_cmd = ["git", "checkout", commit_id]
        result = subprocess.run(checkout_cmd, cwd=repo_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"⚠️ 切换提交失败: {result.stderr}")
        else:
            print("✅ 切换提交成功")
        
        # 3. 显示项目结构
        print(f"\n📁 项目结构:")
        list_directory_tree(repo_dir, max_depth=4)
        
        # 4. 检查关键目录
        key_dirs = [
            "src/main/java",
            "src/test/java",
            "src/main/resources",
            "src/test/resources"
        ]
        
        print(f"\n📋 关键目录检查:")
        for dir_path in key_dirs:
            full_path = os.path.join(repo_dir, dir_path)
            if os.path.exists(full_path):
                file_count = count_files_in_dir(full_path)
                print(f"  ✅ {dir_path}: {file_count} 个文件")
            else:
                print(f"  ❌ {dir_path}: 不存在")
        
        # 5. 查找Java文件
        print(f"\n🔍 查找Java文件:")
        java_files = find_java_files(repo_dir)
        if java_files:
            print(f"  找到 {len(java_files)} 个Java文件:")
            for java_file in java_files[:10]:  # 只显示前10个
                print(f"    📄 {java_file}")
            if len(java_files) > 10:
                print(f"    ... 还有 {len(java_files) - 10} 个文件")
        else:
            print("  ❌ 未找到Java文件")
        
        # 6. 检查pom.xml内容
        pom_path = os.path.join(repo_dir, "pom.xml")
        if os.path.exists(pom_path):
            print(f"\n📄 pom.xml 内容摘要:")
            analyze_pom_content(pom_path)
        
        # 7. 如果项目为空，创建示例代码
        if not java_files:
            print(f"\n🔧 项目为空，创建示例代码...")
            create_sample_code(repo_dir)
            
            # 重新测试Maven
            print(f"\n🧪 测试Maven构建...")
            test_maven_build(repo_dir)
        
    except Exception as e:
        print(f"❌ 检查过程出错: {e}")
    finally:
        # 清理
        try:
            shutil.rmtree(temp_dir)
            print(f"\n🧹 清理临时目录")
        except Exception as e:
            print(f"⚠️ 清理失败: {e}")

def list_directory_tree(path, max_depth=3, current_depth=0, prefix=""):
    """列出目录树"""
    if current_depth >= max_depth:
        return
    
    try:
        items = sorted(os.listdir(path))
        for i, item in enumerate(items):
            if item.startswith('.'):
                continue
                
            item_path = os.path.join(path, item)
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            
            if os.path.isdir(item_path):
                print(f"{prefix}{current_prefix}📁 {item}/")
                next_prefix = prefix + ("    " if is_last else "│   ")
                list_directory_tree(item_path, max_depth, current_depth + 1, next_prefix)
            else:
                size = os.path.getsize(item_path)
                print(f"{prefix}{current_prefix}📄 {item} ({size} bytes)")
    except PermissionError:
        print(f"{prefix}❌ 权限不足")

def count_files_in_dir(dir_path):
    """统计目录中的文件数量"""
    count = 0
    for root, dirs, files in os.walk(dir_path):
        count += len(files)
    return count

def find_java_files(repo_dir):
    """查找Java文件"""
    java_files = []
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            if file.endswith('.java'):
                rel_path = os.path.relpath(os.path.join(root, file), repo_dir)
                java_files.append(rel_path)
    return java_files

def analyze_pom_content(pom_path):
    """分析pom.xml内容"""
    try:
        with open(pom_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"  📏 文件大小: {len(content)} 字符")
        
        # 检查关键元素
        checks = [
            ('groupId', '<groupId>'),
            ('artifactId', '<artifactId>'),
            ('version', '<version>'),
            ('dependencies', '<dependencies>'),
            ('build', '<build>'),
            ('plugins', '<plugins>'),
            ('JaCoCo插件', 'jacoco-maven-plugin')
        ]
        
        for name, pattern in checks:
            if pattern in content:
                print(f"  ✅ {name}: 存在")
            else:
                print(f"  ❌ {name}: 不存在")
                
    except Exception as e:
        print(f"  ❌ 分析失败: {e}")

def create_sample_code(repo_dir):
    """创建示例代码"""
    try:
        # 创建目录结构
        main_java_dir = os.path.join(repo_dir, "src", "main", "java", "com", "example")
        test_java_dir = os.path.join(repo_dir, "src", "test", "java", "com", "example")
        
        os.makedirs(main_java_dir, exist_ok=True)
        os.makedirs(test_java_dir, exist_ok=True)
        
        # 创建主类
        main_class = '''package com.example;

public class Calculator {
    
    public int add(int a, int b) {
        return a + b;
    }
    
    public int subtract(int a, int b) {
        return a - b;
    }
    
    public int multiply(int a, int b) {
        return a * b;
    }
    
    public int divide(int a, int b) {
        if (b == 0) {
            throw new IllegalArgumentException("Division by zero");
        }
        return a / b;
    }
    
    public boolean isEven(int number) {
        return number % 2 == 0;
    }
}'''
        
        with open(os.path.join(main_java_dir, "Calculator.java"), 'w', encoding='utf-8') as f:
            f.write(main_class)
        
        # 创建测试类
        test_class = '''package com.example;

import org.junit.Test;
import static org.junit.Assert.*;

public class CalculatorTest {
    
    private Calculator calculator = new Calculator();
    
    @Test
    public void testAdd() {
        assertEquals(5, calculator.add(2, 3));
        assertEquals(0, calculator.add(-1, 1));
    }
    
    @Test
    public void testSubtract() {
        assertEquals(1, calculator.subtract(3, 2));
        assertEquals(-2, calculator.subtract(-1, 1));
    }
    
    @Test
    public void testMultiply() {
        assertEquals(6, calculator.multiply(2, 3));
        assertEquals(0, calculator.multiply(0, 5));
    }
    
    @Test
    public void testDivide() {
        assertEquals(2, calculator.divide(6, 3));
        assertEquals(0, calculator.divide(0, 5));
    }
    
    @Test(expected = IllegalArgumentException.class)
    public void testDivideByZero() {
        calculator.divide(5, 0);
    }
    
    @Test
    public void testIsEven() {
        assertTrue(calculator.isEven(2));
        assertTrue(calculator.isEven(0));
        assertFalse(calculator.isEven(1));
        assertFalse(calculator.isEven(-1));
    }
}'''
        
        with open(os.path.join(test_java_dir, "CalculatorTest.java"), 'w', encoding='utf-8') as f:
            f.write(test_class)
        
        print("  ✅ 创建了Calculator.java")
        print("  ✅ 创建了CalculatorTest.java")
        
    except Exception as e:
        print(f"  ❌ 创建示例代码失败: {e}")

def test_maven_build(repo_dir):
    """测试Maven构建"""
    try:
        commands = [
            ["mvn", "clean", "compile"],
            ["mvn", "test"],
            ["mvn", "jacoco:report"]
        ]
        
        for cmd in commands:
            print(f"\n▶️ 执行: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, 
                cwd=repo_dir, 
                capture_output=True, 
                text=True, 
                timeout=300
            )
            
            print(f"返回码: {result.returncode}")
            if result.returncode == 0:
                print("✅ 成功")
            else:
                print("❌ 失败")
                print(f"错误: {result.stderr}")
        
        # 查找生成的报告
        target_dir = os.path.join(repo_dir, "target")
        if os.path.exists(target_dir):
            print(f"\n📁 target目录内容:")
            list_directory_tree(target_dir, max_depth=3)
            
            # 查找JaCoCo报告
            jacoco_files = []
            for root, dirs, files in os.walk(target_dir):
                for file in files:
                    if 'jacoco' in file.lower():
                        jacoco_files.append(os.path.join(root, file))
            
            if jacoco_files:
                print(f"\n✅ 找到JaCoCo文件:")
                for file in jacoco_files:
                    print(f"  📄 {file}")
            else:
                print(f"\n❌ 未找到JaCoCo报告")
        
    except Exception as e:
        print(f"❌ Maven测试失败: {e}")

if __name__ == "__main__":
    check_project_structure()
