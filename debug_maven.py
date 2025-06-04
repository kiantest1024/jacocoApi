#!/usr/bin/env python3
"""
调试Maven JaCoCo执行
"""

import os
import subprocess
import tempfile
import shutil
import xml.etree.ElementTree as ET

def clone_and_test_repo():
    """克隆仓库并测试Maven执行"""
    
    repo_url = "http://172.16.1.30/kian/jacocotest.git"
    commit_id = "84d32a75d4832dc26f33678706bc8446da51cda0"
    
    print("🔍 调试Maven JaCoCo执行")
    print("=" * 50)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="debug_maven_")
    repo_dir = os.path.join(temp_dir, "repo")
    
    try:
        # 1. 克隆仓库
        print(f"📥 克隆仓库到: {repo_dir}")
        clone_cmd = ["git", "clone", repo_url, repo_dir]
        result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ 克隆失败: {result.stderr}")
            return
        
        print("✅ 克隆成功")
        
        # 2. 切换提交
        print(f"🔄 切换到提交: {commit_id}")
        checkout_cmd = ["git", "checkout", commit_id]
        result = subprocess.run(checkout_cmd, cwd=repo_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"⚠️ 切换提交失败: {result.stderr}")
        else:
            print("✅ 切换提交成功")
        
        # 3. 检查pom.xml
        pom_path = os.path.join(repo_dir, "pom.xml")
        if not os.path.exists(pom_path):
            print("❌ 未找到pom.xml")
            return
        
        print("✅ 找到pom.xml")
        
        # 4. 分析原始pom.xml
        print("\n📋 分析原始pom.xml...")
        analyze_pom(pom_path)
        
        # 5. 备份并增强pom.xml
        print("\n🔧 增强pom.xml...")
        pom_backup = os.path.join(repo_dir, "pom.xml.backup")
        shutil.copy2(pom_path, pom_backup)
        
        try:
            enhance_pom_for_jacoco(pom_path)
            print("✅ pom.xml增强成功")
        except Exception as e:
            print(f"❌ pom.xml增强失败: {e}")
        
        # 6. 显示增强后的pom.xml
        print("\n📋 分析增强后的pom.xml...")
        analyze_pom(pom_path)
        
        # 7. 执行Maven命令
        print("\n🔨 执行Maven命令...")
        
        maven_commands = [
            ["mvn", "clean"],
            ["mvn", "compile"],
            ["mvn", "test-compile"],
            ["mvn", "test", "-Dmaven.test.failure.ignore=true"],
            ["mvn", "jacoco:report"]
        ]
        
        for cmd in maven_commands:
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
                print(f"错误输出: {result.stderr}")
            
            # 显示部分输出
            if result.stdout:
                lines = result.stdout.split('\n')
                print("输出摘要:")
                for line in lines[-10:]:  # 显示最后10行
                    if line.strip():
                        print(f"  {line}")
        
        # 8. 查找生成的文件
        print(f"\n🔍 查找生成的文件...")
        target_dir = os.path.join(repo_dir, "target")
        if os.path.exists(target_dir):
            print(f"📁 target目录内容:")
            list_directory_tree(target_dir, max_depth=3)
        else:
            print("❌ target目录不存在")
        
        # 9. 查找JaCoCo报告
        print(f"\n🔍 查找JaCoCo报告...")
        jacoco_files = find_jacoco_files(repo_dir)
        if jacoco_files:
            print("✅ 找到JaCoCo文件:")
            for file in jacoco_files:
                print(f"  📄 {file}")
        else:
            print("❌ 未找到JaCoCo报告文件")
        
    except Exception as e:
        print(f"❌ 调试过程出错: {e}")
    finally:
        # 清理
        try:
            shutil.rmtree(temp_dir)
            print(f"\n🧹 清理临时目录: {temp_dir}")
        except Exception as e:
            print(f"⚠️ 清理失败: {e}")

def analyze_pom(pom_path):
    """分析pom.xml内容"""
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        
        # 查找JaCoCo插件
        jacoco_found = False
        for plugin in root.findall(".//plugin"):
            artifact_id = plugin.find(".//artifactId")
            if artifact_id is not None and "jacoco" in artifact_id.text.lower():
                jacoco_found = True
                print(f"  ✅ 找到JaCoCo插件: {artifact_id.text}")
                break
        
        if not jacoco_found:
            print("  ❌ 未找到JaCoCo插件")
        
        # 查找测试
        test_source_dir = root.find(".//testSourceDirectory")
        if test_source_dir is not None:
            print(f"  📁 测试源目录: {test_source_dir.text}")
        
        # 查找依赖
        dependencies = root.findall(".//dependency")
        test_deps = 0
        for dep in dependencies:
            scope = dep.find("scope")
            if scope is not None and scope.text == "test":
                test_deps += 1
        
        print(f"  📦 总依赖数: {len(dependencies)}")
        print(f"  🧪 测试依赖数: {test_deps}")
        
    except Exception as e:
        print(f"  ❌ 分析pom.xml失败: {e}")

def enhance_pom_for_jacoco(pom_path):
    """增强pom.xml以支持JaCoCo"""
    tree = ET.parse(pom_path)
    root = tree.getroot()

    # 获取命名空间
    namespace = ''
    if root.tag.startswith('{'):
        namespace = root.tag[1:root.tag.index('}')]
        ET.register_namespace('', namespace)

    # 查找properties节点（直接子节点，避免重复）
    properties = None
    for child in root:
        if child.tag.endswith('properties'):
            properties = child
            print("  ✅ 找到现有properties节点")
            break

    if properties is None:
        # 在适当位置插入properties节点
        insert_index = 0
        for i, child in enumerate(root):
            if child.tag.endswith(('groupId', 'artifactId', 'version', 'packaging')):
                insert_index = i + 1

        properties = ET.Element('properties')
        root.insert(insert_index, properties)
        print("  ✅ 创建properties节点")

    # 添加JaCoCo版本属性
    jacoco_version_found = False
    for prop in properties:
        if prop.tag == 'jacoco.version':
            jacoco_version_found = True
            print("  ✅ JaCoCo版本属性已存在")
            break

    if not jacoco_version_found:
        jacoco_version = ET.SubElement(properties, 'jacoco.version')
        jacoco_version.text = '0.8.7'
        print("  ✅ 添加JaCoCo版本属性")

    # 查找build节点
    build = None
    for child in root:
        if child.tag.endswith('build'):
            build = child
            print("  ✅ 找到现有build节点")
            break

    if build is None:
        build = ET.SubElement(root, 'build')
        print("  ✅ 创建build节点")

    # 查找plugins节点
    plugins = None
    for child in build:
        if child.tag.endswith('plugins'):
            plugins = child
            print("  ✅ 找到现有plugins节点")
            break

    if plugins is None:
        plugins = ET.SubElement(build, 'plugins')
        print("  ✅ 创建plugins节点")

    # 检查是否已有JaCoCo插件
    jacoco_plugin_exists = False
    for plugin in plugins:
        if plugin.tag.endswith('plugin'):
            for child in plugin:
                if child.tag.endswith('artifactId') and child.text == 'jacoco-maven-plugin':
                    jacoco_plugin_exists = True
                    print("  ✅ JaCoCo插件已存在")
                    break
            if jacoco_plugin_exists:
                break

    if not jacoco_plugin_exists:
        # 添加JaCoCo插件
        jacoco_plugin = ET.SubElement(plugins, 'plugin')

        group_id = ET.SubElement(jacoco_plugin, 'groupId')
        group_id.text = 'org.jacoco'

        artifact_id = ET.SubElement(jacoco_plugin, 'artifactId')
        artifact_id.text = 'jacoco-maven-plugin'

        version = ET.SubElement(jacoco_plugin, 'version')
        version.text = '${jacoco.version}'

        executions = ET.SubElement(jacoco_plugin, 'executions')

        # prepare-agent
        execution1 = ET.SubElement(executions, 'execution')
        ex1_id = ET.SubElement(execution1, 'id')
        ex1_id.text = 'prepare-agent'
        goals1 = ET.SubElement(execution1, 'goals')
        goal1 = ET.SubElement(goals1, 'goal')
        goal1.text = 'prepare-agent'

        # report
        execution2 = ET.SubElement(executions, 'execution')
        ex2_id = ET.SubElement(execution2, 'id')
        ex2_id.text = 'report'
        ex2_phase = ET.SubElement(execution2, 'phase')
        ex2_phase.text = 'test'
        goals2 = ET.SubElement(execution2, 'goals')
        goal2 = ET.SubElement(goals2, 'goal')
        goal2.text = 'report'

        print("  ✅ 添加JaCoCo插件配置")

    # 写回文件
    tree.write(pom_path, encoding='utf-8', xml_declaration=True)

def list_directory_tree(path, max_depth=2, current_depth=0):
    """列出目录树"""
    if current_depth >= max_depth:
        return
    
    try:
        items = sorted(os.listdir(path))
        for item in items:
            item_path = os.path.join(path, item)
            indent = "  " * current_depth
            if os.path.isdir(item_path):
                print(f"{indent}📁 {item}/")
                list_directory_tree(item_path, max_depth, current_depth + 1)
            else:
                size = os.path.getsize(item_path)
                print(f"{indent}📄 {item} ({size} bytes)")
    except PermissionError:
        print(f"{indent}❌ 权限不足")

def find_jacoco_files(repo_dir):
    """查找JaCoCo相关文件"""
    jacoco_files = []
    
    for root, _, files in os.walk(repo_dir):
        for file in files:
            if 'jacoco' in file.lower() or file.endswith('.exec'):
                jacoco_files.append(os.path.join(root, file))
    
    return jacoco_files

if __name__ == "__main__":
    clone_and_test_repo()
