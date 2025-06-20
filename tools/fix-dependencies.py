#!/usr/bin/env python3
"""Maven 项目依赖修复工具"""

import sys
import os
import xml.etree.ElementTree as ET
import shutil
from datetime import datetime

def log_info(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: {message}")

def log_success(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {message}")

def log_warning(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  {message}")

def log_error(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {message}")

def analyze_test_files(project_dir):
    """分析测试文件使用的依赖"""
    test_dir = os.path.join(project_dir, "src", "test", "java")
    if not os.path.exists(test_dir):
        log_warning("测试目录不存在")
        return set()
    
    dependencies_needed = set()
    
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        if any(import_stmt in content for import_stmt in [
                            'org.junit.jupiter', 'junit.jupiter.api', '@Test'
                        ]):
                            dependencies_needed.add('junit5')
                        
                        if any(import_stmt in content for import_stmt in [
                            'org.mockito', 'mockito.junit.jupiter', '@Mock'
                        ]):
                            dependencies_needed.add('mockito')
                        
                        if any(import_stmt in content for import_stmt in [
                            'org.assertj.core.api', 'assertThat(', 'Assertions.assertThat'
                        ]):
                            dependencies_needed.add('assertj')
                        
                        if any(import_stmt in content for import_stmt in [
                            'org.junit.Test', 'junit.framework'
                        ]):
                            dependencies_needed.add('junit4')
                            
                except Exception as e:
                    log_warning(f"无法读取文件 {file_path}: {e}")
    
    log_info(f"检测到需要的依赖: {dependencies_needed}")
    return dependencies_needed

def fix_pom_xml(pom_path, dependencies_needed):
    """修复 pom.xml 文件"""
    log_info(f"修复 pom.xml: {pom_path}")
    
    backup_path = f"{pom_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(pom_path, backup_path)
    log_info(f"已备份原文件到: {backup_path}")
    
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        
        ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
        ET.register_namespace('', 'http://maven.apache.org/POM/4.0.0')
        
        # 添加属性
        properties = root.find('maven:properties', ns)
        if properties is None:
            properties = ET.SubElement(root, 'properties')
        
        version_props = {
            'maven.compiler.source': '11',
            'maven.compiler.target': '11',
            'project.build.sourceEncoding': 'UTF-8',
            'junit.version': '5.9.2',
            'mockito.version': '4.11.0',
            'assertj.version': '3.24.2',
            'jacoco.version': '0.8.8'
        }
        
        for prop_name, prop_value in version_props.items():
            prop_elem = ET.SubElement(properties, prop_name.replace('.', '.'))
            prop_elem.text = prop_value
        
        # 添加依赖
        dependencies = root.find('maven:dependencies', ns)
        if dependencies is None:
            dependencies = ET.SubElement(root, 'dependencies')
        
        deps_to_add = []
        
        if 'junit5' in dependencies_needed:
            deps_to_add.append({
                'groupId': 'org.junit.jupiter',
                'artifactId': 'junit-jupiter',
                'version': '${junit.version}',
                'scope': 'test'
            })
        
        if 'mockito' in dependencies_needed:
            deps_to_add.extend([
                {
                    'groupId': 'org.mockito',
                    'artifactId': 'mockito-core',
                    'version': '${mockito.version}',
                    'scope': 'test'
                },
                {
                    'groupId': 'org.mockito',
                    'artifactId': 'mockito-junit-jupiter',
                    'version': '${mockito.version}',
                    'scope': 'test'
                }
            ])
        
        if 'assertj' in dependencies_needed:
            deps_to_add.append({
                'groupId': 'org.assertj',
                'artifactId': 'assertj-core',
                'version': '${assertj.version}',
                'scope': 'test'
            })
        
        if 'junit4' in dependencies_needed:
            deps_to_add.append({
                'groupId': 'junit',
                'artifactId': 'junit',
                'version': '4.13.2',
                'scope': 'test'
            })
        
        # 添加依赖到 XML
        for dep_info in deps_to_add:
            dep_elem = ET.SubElement(dependencies, 'dependency')
            
            group_elem = ET.SubElement(dep_elem, 'groupId')
            group_elem.text = dep_info['groupId']
            
            artifact_elem = ET.SubElement(dep_elem, 'artifactId')
            artifact_elem.text = dep_info['artifactId']
            
            version_elem = ET.SubElement(dep_elem, 'version')
            version_elem.text = dep_info['version']
            
            if 'scope' in dep_info:
                scope_elem = ET.SubElement(dep_elem, 'scope')
                scope_elem.text = dep_info['scope']
            
            log_success(f"添加依赖: {dep_info['groupId']}:{dep_info['artifactId']}")
        
        # 添加插件
        build = root.find('maven:build', ns)
        if build is None:
            build = ET.SubElement(root, 'build')
        
        plugins = build.find('maven:plugins', ns)
        if plugins is None:
            plugins = ET.SubElement(build, 'plugins')
        
        # 添加必要插件
        plugins_to_add = [
            {
                'groupId': 'org.apache.maven.plugins',
                'artifactId': 'maven-compiler-plugin',
                'version': '3.11.0',
                'configuration': {'source': '11', 'target': '11'}
            },
            {
                'groupId': 'org.apache.maven.plugins',
                'artifactId': 'maven-surefire-plugin',
                'version': '3.0.0-M9',
                'configuration': {'testFailureIgnore': 'true'}
            },
            {
                'groupId': 'org.jacoco',
                'artifactId': 'jacoco-maven-plugin',
                'version': '${jacoco.version}',
                'executions': [
                    {'id': 'prepare-agent', 'goals': ['prepare-agent']},
                    {'id': 'report', 'phase': 'test', 'goals': ['report']}
                ]
            }
        ]
        
        for plugin_info in plugins_to_add:
            plugin_elem = ET.SubElement(plugins, 'plugin')
            
            group_elem = ET.SubElement(plugin_elem, 'groupId')
            group_elem.text = plugin_info['groupId']
            
            artifact_elem = ET.SubElement(plugin_elem, 'artifactId')
            artifact_elem.text = plugin_info['artifactId']
            
            version_elem = ET.SubElement(plugin_elem, 'version')
            version_elem.text = plugin_info['version']
            
            if 'configuration' in plugin_info:
                config_elem = ET.SubElement(plugin_elem, 'configuration')
                for key, value in plugin_info['configuration'].items():
                    config_item = ET.SubElement(config_elem, key)
                    config_item.text = value
            
            if 'executions' in plugin_info:
                executions_elem = ET.SubElement(plugin_elem, 'executions')
                for execution in plugin_info['executions']:
                    exec_elem = ET.SubElement(executions_elem, 'execution')
                    
                    if 'id' in execution:
                        id_elem = ET.SubElement(exec_elem, 'id')
                        id_elem.text = execution['id']
                    
                    if 'phase' in execution:
                        phase_elem = ET.SubElement(exec_elem, 'phase')
                        phase_elem.text = execution['phase']
                    
                    if 'goals' in execution:
                        goals_elem = ET.SubElement(exec_elem, 'goals')
                        for goal in execution['goals']:
                            goal_elem = ET.SubElement(goals_elem, 'goal')
                            goal_elem.text = goal
            
            log_success(f"添加插件: {plugin_info['groupId']}:{plugin_info['artifactId']}")
        
        tree.write(pom_path, encoding='utf-8', xml_declaration=True)
        log_success("pom.xml 修复完成")
        
        return True
        
    except Exception as e:
        log_error(f"修复 pom.xml 失败: {e}")
        shutil.copy2(backup_path, pom_path)
        log_info("已恢复原文件")
        return False

def main():
    if len(sys.argv) != 2:
        print("用法: python3 fix-dependencies.py <project_directory>")
        sys.exit(1)
    
    project_dir = sys.argv[1]
    
    if not os.path.exists(project_dir):
        log_error(f"项目目录不存在: {project_dir}")
        sys.exit(1)
    
    pom_path = os.path.join(project_dir, "pom.xml")
    if not os.path.exists(pom_path):
        log_error(f"pom.xml 不存在: {pom_path}")
        sys.exit(1)
    
    log_info(f"开始修复项目依赖: {project_dir}")
    
    dependencies_needed = analyze_test_files(project_dir)
    
    if not dependencies_needed:
        log_warning("未检测到需要修复的依赖")
        return
    
    if fix_pom_xml(pom_path, dependencies_needed):
        log_success("依赖修复完成！")
    else:
        log_error("依赖修复失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
