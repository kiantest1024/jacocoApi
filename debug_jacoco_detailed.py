#!/usr/bin/env python3
"""
详细的JaCoCo调试脚本
"""

import os
import subprocess
import tempfile
import shutil
import time

def debug_jacoco_scan():
    """详细调试JaCoCo扫描过程"""
    
    repo_url = "http://172.16.1.30/kian/jacocotest.git"
    commit_id = "84d32a75d4832dc26f33678706bc8446da51cda0"
    
    print("🔍 详细JaCoCo扫描调试")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="debug_jacoco_detailed_")
    repo_dir = os.path.join(temp_dir, "repo")
    
    print(f"📁 临时目录: {temp_dir}")
    print(f"📁 仓库目录: {repo_dir}")
    
    try:
        # 1. 克隆仓库
        print(f"\n📥 步骤1: 克隆仓库")
        clone_cmd = ["git", "clone", repo_url, repo_dir]
        result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ 克隆失败: {result.stderr}")
            return
        
        print("✅ 克隆成功")
        
        # 2. 切换提交
        print(f"\n🔄 步骤2: 切换提交")
        checkout_cmd = ["git", "checkout", commit_id]
        result = subprocess.run(checkout_cmd, cwd=repo_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"⚠️ 切换提交失败: {result.stderr}")
        else:
            print("✅ 切换提交成功")
        
        # 3. 检查项目结构
        print(f"\n📋 步骤3: 检查项目结构")
        check_project_structure(repo_dir)
        
        # 4. 检查原始pom.xml
        print(f"\n📄 步骤4: 检查原始pom.xml")
        pom_path = os.path.join(repo_dir, "pom.xml")
        if os.path.exists(pom_path):
            with open(pom_path, 'r', encoding='utf-8') as f:
                pom_content = f.read()
            print(f"原始pom.xml大小: {len(pom_content)} 字符")
            print("原始pom.xml内容:")
            print("-" * 40)
            print(pom_content)
            print("-" * 40)
        else:
            print("❌ pom.xml不存在")
            return
        
        # 5. 增强pom.xml
        print(f"\n🔧 步骤5: 增强pom.xml")
        pom_backup = os.path.join(repo_dir, "pom.xml.backup")
        shutil.copy2(pom_path, pom_backup)
        
        enhance_result = enhance_pom_detailed(pom_path)
        if enhance_result:
            print("✅ pom.xml增强成功")
            
            # 显示增强后的pom.xml
            with open(pom_path, 'r', encoding='utf-8') as f:
                enhanced_content = f.read()
            print(f"增强后pom.xml大小: {len(enhanced_content)} 字符")
            print("增强后pom.xml内容:")
            print("-" * 40)
            print(enhanced_content)
            print("-" * 40)
        else:
            print("❌ pom.xml增强失败")
            return
        
        # 6. 创建示例代码（如果需要）
        print(f"\n📝 步骤6: 检查并创建示例代码")
        create_sample_code_if_needed(repo_dir)
        
        # 7. 执行Maven命令
        print(f"\n🔨 步骤7: 执行Maven命令")
        maven_commands = [
            ["mvn", "clean"],
            ["mvn", "compile"],
            ["mvn", "test-compile"],
            ["mvn", "test", "-Dmaven.test.failure.ignore=true"],
            ["mvn", "jacoco:report"]
        ]
        
        for i, cmd in enumerate(maven_commands, 1):
            print(f"\n▶️ 7.{i} 执行: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, 
                cwd=repo_dir, 
                capture_output=True, 
                text=True, 
                timeout=300
            )
            
            print(f"返回码: {result.returncode}")
            
            if result.stdout:
                print("标准输出:")
                print(result.stdout)
            
            if result.stderr:
                print("错误输出:")
                print(result.stderr)
            
            if result.returncode == 0:
                print("✅ 成功")
            else:
                print("❌ 失败")
                # 继续执行其他命令
        
        # 8. 检查target目录
        print(f"\n📁 步骤8: 检查target目录")
        target_dir = os.path.join(repo_dir, "target")
        if os.path.exists(target_dir):
            print("✅ target目录存在")
            print("target目录结构:")
            list_directory_tree(target_dir, max_depth=4)
        else:
            print("❌ target目录不存在")
        
        # 9. 查找JaCoCo文件
        print(f"\n🔍 步骤9: 查找JaCoCo文件")
        jacoco_files = find_all_jacoco_files(repo_dir)
        if jacoco_files:
            print(f"✅ 找到 {len(jacoco_files)} 个JaCoCo相关文件:")
            for file_path in jacoco_files:
                file_size = os.path.getsize(file_path)
                rel_path = os.path.relpath(file_path, repo_dir)
                print(f"  📄 {rel_path} ({file_size} bytes)")
                
                # 如果是XML文件，显示内容摘要
                if file_path.endswith('.xml'):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            xml_content = f.read()
                        print(f"    XML内容长度: {len(xml_content)} 字符")
                        if 'coverage' in xml_content.lower():
                            print("    ✅ 包含覆盖率数据")
                        else:
                            print("    ❌ 不包含覆盖率数据")
                    except Exception as e:
                        print(f"    ❌ 读取XML失败: {e}")
        else:
            print("❌ 未找到JaCoCo文件")
        
        # 10. 保留目录供手动检查
        print(f"\n📋 步骤10: 调试信息")
        print(f"临时目录保留: {temp_dir}")
        print(f"手动检查命令:")
        print(f"  cd {repo_dir}")
        print(f"  ls -la")
        print(f"  find . -name '*jacoco*'")
        print(f"  mvn clean test jacoco:report")
        print(f"\n清理命令:")
        print(f"  rm -rf {temp_dir}")
        
        # 等待用户输入
        input("\n按回车键继续（目录将被保留）...")
        
    except Exception as e:
        print(f"❌ 调试过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 不自动清理，让用户手动检查
    print(f"\n📁 临时目录保留用于手动检查: {temp_dir}")

def check_project_structure(repo_dir):
    """检查项目结构"""
    print("项目结构:")
    list_directory_tree(repo_dir, max_depth=3)
    
    # 检查关键目录
    key_dirs = ["src/main/java", "src/test/java", "src/main/resources", "src/test/resources"]
    print("\n关键目录:")
    for dir_path in key_dirs:
        full_path = os.path.join(repo_dir, dir_path)
        if os.path.exists(full_path):
            file_count = sum(len(files) for _, _, files in os.walk(full_path))
            print(f"  ✅ {dir_path}: {file_count} 个文件")
        else:
            print(f"  ❌ {dir_path}: 不存在")

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

def enhance_pom_detailed(pom_path):
    """详细的pom.xml增强"""
    try:
        import re
        
        print("读取pom.xml...")
        with open(pom_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"原始内容长度: {len(content)} 字符")
        
        # 检查现有内容
        has_jacoco = 'jacoco-maven-plugin' in content
        has_junit = 'junit' in content.lower()
        has_properties = '<properties>' in content
        has_dependencies = '<dependencies>' in content
        has_build = '<build>' in content
        has_plugins = '<plugins>' in content
        
        print(f"现有内容检查:")
        print(f"  JaCoCo插件: {'✅' if has_jacoco else '❌'}")
        print(f"  JUnit依赖: {'✅' if has_junit else '❌'}")
        print(f"  Properties: {'✅' if has_properties else '❌'}")
        print(f"  Dependencies: {'✅' if has_dependencies else '❌'}")
        print(f"  Build: {'✅' if has_build else '❌'}")
        print(f"  Plugins: {'✅' if has_plugins else '❌'}")
        
        if has_jacoco:
            print("JaCoCo插件已存在，跳过增强")
            return True
        
        # 添加JUnit依赖
        if not has_junit:
            print("添加JUnit依赖...")
            junit_dependency = '''
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>'''
            
            if has_dependencies:
                content = content.replace('<dependencies>', f'<dependencies>{junit_dependency}')
                print("  ✅ 在现有dependencies中添加JUnit")
            else:
                dependencies_block = f'''
    <dependencies>{junit_dependency}
    </dependencies>'''
                
                if '</version>' in content:
                    version_pattern = r'(\s*</version>\s*)'
                    content = re.sub(version_pattern, r'\1' + dependencies_block, content, count=1)
                    print("  ✅ 创建dependencies节点并添加JUnit")
        
        # 添加JaCoCo属性
        print("添加JaCoCo属性...")
        jacoco_property = '<jacoco.version>0.8.7</jacoco.version>'
        
        if has_properties:
            content = content.replace('<properties>', f'<properties>\n        {jacoco_property}')
            print("  ✅ 在现有properties中添加JaCoCo版本")
        else:
            properties_block = f'''
    <properties>
        {jacoco_property}
    </properties>'''
            
            if '</dependencies>' in content:
                content = content.replace('</dependencies>', f'</dependencies>{properties_block}')
            elif '</version>' in content:
                version_pattern = r'(\s*</version>\s*)'
                content = re.sub(version_pattern, r'\1' + properties_block, content, count=1)
            print("  ✅ 创建properties节点并添加JaCoCo版本")
        
        # 添加JaCoCo插件
        print("添加JaCoCo插件...")
        jacoco_plugin = '''
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>${jacoco.version}</version>
                <executions>
                    <execution>
                        <id>prepare-agent</id>
                        <goals>
                            <goal>prepare-agent</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>report</id>
                        <phase>test</phase>
                        <goals>
                            <goal>report</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>'''
        
        if has_plugins:
            content = content.replace('<plugins>', f'<plugins>{jacoco_plugin}')
            print("  ✅ 在现有plugins中添加JaCoCo插件")
        elif has_build:
            plugins_block = f'''
        <plugins>{jacoco_plugin}
        </plugins>'''
            content = content.replace('<build>', f'<build>{plugins_block}')
            print("  ✅ 在build中创建plugins并添加JaCoCo插件")
        else:
            build_block = f'''
    <build>
        <plugins>{jacoco_plugin}
        </plugins>
    </build>'''
            
            if '</dependencies>' in content:
                content = content.replace('</dependencies>', f'</dependencies>{build_block}')
            elif '</properties>' in content:
                content = content.replace('</properties>', f'</properties>{build_block}')
            else:
                content = content.replace('</project>', f'{build_block}\n</project>')
            print("  ✅ 创建完整的build节点并添加JaCoCo插件")
        
        # 写回文件
        with open(pom_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"增强完成，新内容长度: {len(content)} 字符")
        return True
        
    except Exception as e:
        print(f"增强失败: {e}")
        return False

def create_sample_code_if_needed(repo_dir):
    """如果需要，创建示例代码"""
    src_main_java = os.path.join(repo_dir, "src", "main", "java")
    src_test_java = os.path.join(repo_dir, "src", "test", "java")
    
    # 检查是否有Java文件
    has_main_java = False
    has_test_java = False
    
    if os.path.exists(src_main_java):
        for root, dirs, files in os.walk(src_main_java):
            if any(f.endswith('.java') for f in files):
                has_main_java = True
                break
    
    if os.path.exists(src_test_java):
        for root, dirs, files in os.walk(src_test_java):
            if any(f.endswith('.java') for f in files):
                has_test_java = True
                break
    
    print(f"Java代码检查:")
    print(f"  主代码: {'✅' if has_main_java else '❌'}")
    print(f"  测试代码: {'✅' if has_test_java else '❌'}")
    
    if not has_main_java or not has_test_java:
        print("创建示例代码...")
        
        # 创建目录
        main_pkg_dir = os.path.join(src_main_java, "com", "example")
        test_pkg_dir = os.path.join(src_test_java, "com", "example")
        os.makedirs(main_pkg_dir, exist_ok=True)
        os.makedirs(test_pkg_dir, exist_ok=True)
        
        # 创建主类
        if not has_main_java:
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
}'''
            
            with open(os.path.join(main_pkg_dir, "Calculator.java"), 'w', encoding='utf-8') as f:
                f.write(main_class)
            print("  ✅ 创建Calculator.java")
        
        # 创建测试类
        if not has_test_java:
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
    }
    
    @Test
    public void testMultiply() {
        assertEquals(6, calculator.multiply(2, 3));
    }
    
    @Test
    public void testDivide() {
        assertEquals(2, calculator.divide(6, 3));
    }
    
    @Test(expected = IllegalArgumentException.class)
    public void testDivideByZero() {
        calculator.divide(5, 0);
    }
}'''
            
            with open(os.path.join(test_pkg_dir, "CalculatorTest.java"), 'w', encoding='utf-8') as f:
                f.write(test_class)
            print("  ✅ 创建CalculatorTest.java")

def find_all_jacoco_files(repo_dir):
    """查找所有JaCoCo相关文件"""
    jacoco_files = []
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            if 'jacoco' in file.lower() or file.endswith('.exec'):
                jacoco_files.append(os.path.join(root, file))
    return jacoco_files

if __name__ == "__main__":
    debug_jacoco_scan()
