#!/usr/bin/env python3
"""
测试代码分析和修复工具
专门分析和修复 Java 测试代码的编译错误
"""

import os
import re
import sys
import tempfile
import subprocess
from pathlib import Path

def analyze_java_file(file_path):
    """分析 Java 文件的问题"""
    print(f"\n🔍 分析文件: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return []
    
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        file_name = os.path.basename(file_path)
        class_name_from_file = file_name.replace('.java', '')
        
        # 1. 检查类名与文件名是否匹配
        public_class_pattern = r'public\s+class\s+(\w+)'
        matches = re.findall(public_class_pattern, content)
        
        if matches:
            actual_class_name = matches[0]
            if actual_class_name != class_name_from_file:
                issues.append({
                    'type': 'naming_mismatch',
                    'severity': 'error',
                    'message': f"类名 '{actual_class_name}' 与文件名 '{class_name_from_file}' 不匹配",
                    'suggestion': f"将文件重命名为 '{actual_class_name}.java' 或将类名改为 '{class_name_from_file}'"
                })
        
        # 2. 检查常见的导入问题
        import_lines = [line for line in lines if line.strip().startswith('import')]
        
        # 检查是否缺少常见的测试导入
        common_test_imports = {
            '@Test': 'import org.junit.jupiter.api.Test;',
            'assertEquals': 'import static org.junit.jupiter.api.Assertions.*;',
            'assertTrue': 'import static org.junit.jupiter.api.Assertions.*;',
            'assertFalse': 'import static org.junit.jupiter.api.Assertions.*;',
            'assertNotNull': 'import static org.junit.jupiter.api.Assertions.*;',
            'Mock': 'import org.mockito.Mock;',
            'MockitoExtension': 'import org.mockito.junit.jupiter.MockitoExtension;',
            'ExtendWith': 'import org.junit.jupiter.api.extension.ExtendWith;'
        }
        
        for annotation, required_import in common_test_imports.items():
            if annotation in content and required_import not in content:
                issues.append({
                    'type': 'missing_import',
                    'severity': 'error',
                    'message': f"使用了 '{annotation}' 但缺少导入语句",
                    'suggestion': f"添加导入: {required_import}"
                })
        
        # 3. 检查测试方法结构
        test_methods = re.findall(r'@Test\s+public\s+void\s+(\w+)\s*\(', content)
        if not test_methods:
            issues.append({
                'type': 'no_test_methods',
                'severity': 'warning',
                'message': "未找到标准的测试方法",
                'suggestion': "确保测试方法使用 @Test 注解并且是 public void"
            })
        
        # 4. 检查包声明
        package_pattern = r'package\s+([\w\.]+);'
        package_match = re.search(package_pattern, content)
        
        if package_match:
            declared_package = package_match.group(1)
            # 根据文件路径推断应该的包名
            path_parts = Path(file_path).parts
            if 'java' in path_parts:
                java_index = path_parts.index('java')
                if java_index + 1 < len(path_parts):
                    expected_package_parts = path_parts[java_index + 1:-1]  # 排除文件名
                    expected_package = '.'.join(expected_package_parts)
                    
                    if expected_package and declared_package != expected_package:
                        issues.append({
                            'type': 'package_mismatch',
                            'severity': 'error',
                            'message': f"包声明 '{declared_package}' 与目录结构不匹配",
                            'suggestion': f"应该是: package {expected_package};"
                        })
        
        # 5. 检查常见的语法问题
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # 检查未闭合的括号
            if line.count('(') != line.count(')'):
                issues.append({
                    'type': 'syntax_error',
                    'severity': 'error',
                    'line': i,
                    'message': f"第 {i} 行: 括号不匹配",
                    'suggestion': "检查括号是否正确闭合"
                })
            
            # 检查缺少分号
            if (line.endswith(')') or line.endswith('"')) and not line.endswith(';') and not line.endswith('{') and not line.endswith('}'):
                if not any(keyword in line for keyword in ['if', 'for', 'while', 'try', 'catch', 'class', 'interface']):
                    issues.append({
                        'type': 'syntax_error',
                        'severity': 'warning',
                        'line': i,
                        'message': f"第 {i} 行: 可能缺少分号",
                        'suggestion': "检查语句是否需要分号结尾"
                    })
    
    except Exception as e:
        issues.append({
            'type': 'analysis_error',
            'severity': 'error',
            'message': f"分析文件时出错: {e}",
            'suggestion': "检查文件编码和格式"
        })
    
    return issues

def generate_fixed_file(file_path, issues):
    """根据问题生成修复后的文件"""
    print(f"\n🔧 生成修复建议: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        fixed_content = content
        suggestions = []
        
        for issue in issues:
            if issue['type'] == 'naming_mismatch':
                # 建议重命名文件
                file_name = os.path.basename(file_path)
                class_name_match = re.search(r'public\s+class\s+(\w+)', content)
                if class_name_match:
                    correct_class_name = class_name_match.group(1)
                    new_file_name = f"{correct_class_name}.java"
                    suggestions.append(f"重命名文件: {file_name} → {new_file_name}")
            
            elif issue['type'] == 'missing_import':
                # 添加缺失的导入
                import_line = issue['suggestion'].replace('添加导入: ', '')
                if import_line not in fixed_content:
                    # 在包声明后添加导入
                    package_match = re.search(r'(package\s+[\w\.]+;\s*\n)', fixed_content)
                    if package_match:
                        insert_pos = package_match.end()
                        fixed_content = fixed_content[:insert_pos] + f"\n{import_line}\n" + fixed_content[insert_pos:]
                    else:
                        # 在文件开头添加导入
                        fixed_content = f"{import_line}\n\n" + fixed_content
                    suggestions.append(f"添加导入: {import_line}")
        
        return fixed_content, suggestions
    
    except Exception as e:
        print(f"❌ 生成修复文件时出错: {e}")
        return None, []

def analyze_project_test_files(project_dir):
    """分析项目中的所有测试文件"""
    print(f"🔍 分析项目测试文件: {project_dir}")
    
    test_files = []
    
    # 查找测试文件
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.java') and ('test' in root.lower() or 'Test' in file):
                test_files.append(os.path.join(root, file))
    
    print(f"📋 找到 {len(test_files)} 个测试文件")
    
    all_issues = {}
    
    for test_file in test_files:
        issues = analyze_java_file(test_file)
        if issues:
            all_issues[test_file] = issues
    
    return all_issues

def print_analysis_report(all_issues):
    """打印分析报告"""
    print("\n" + "="*60)
    print("📊 测试代码分析报告")
    print("="*60)
    
    if not all_issues:
        print("✅ 未发现明显问题")
        return
    
    total_errors = 0
    total_warnings = 0
    
    for file_path, issues in all_issues.items():
        print(f"\n📄 文件: {os.path.relpath(file_path)}")
        print("-" * 40)
        
        for issue in issues:
            severity_icon = "🔴" if issue['severity'] == 'error' else "🟡"
            total_errors += 1 if issue['severity'] == 'error' else 0
            total_warnings += 1 if issue['severity'] == 'warning' else 0
            
            print(f"{severity_icon} {issue['message']}")
            if 'line' in issue:
                print(f"   📍 行号: {issue['line']}")
            print(f"   💡 建议: {issue['suggestion']}")
            print()
    
    print("="*60)
    print(f"📈 总计: {total_errors} 个错误, {total_warnings} 个警告")
    
    if total_errors > 0:
        print("🔴 需要修复错误才能编译通过")
    elif total_warnings > 0:
        print("🟡 建议修复警告以提高代码质量")
    else:
        print("✅ 代码质量良好")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python test-code-analyzer.py <项目目录或Java文件>")
        print("示例: python test-code-analyzer.py /path/to/project")
        print("示例: python test-code-analyzer.py /path/to/TestFile.java")
        sys.exit(1)
    
    target_path = sys.argv[1]
    
    if not os.path.exists(target_path):
        print(f"❌ 路径不存在: {target_path}")
        sys.exit(1)
    
    print("🔍 Java 测试代码分析工具")
    print("="*40)
    
    if os.path.isfile(target_path) and target_path.endswith('.java'):
        # 分析单个文件
        issues = analyze_java_file(target_path)
        all_issues = {target_path: issues} if issues else {}
    else:
        # 分析整个项目
        all_issues = analyze_project_test_files(target_path)
    
    print_analysis_report(all_issues)
    
    # 生成修复建议
    if all_issues:
        print("\n🔧 修复建议:")
        print("-" * 40)
        
        for file_path, issues in all_issues.items():
            fixed_content, suggestions = generate_fixed_file(file_path, issues)
            
            if suggestions:
                print(f"\n📄 {os.path.relpath(file_path)}:")
                for suggestion in suggestions:
                    print(f"  💡 {suggestion}")
                
                # 询问是否保存修复后的文件
                response = input(f"\n是否保存修复后的文件? (y/N): ").strip().lower()
                if response == 'y':
                    backup_path = f"{file_path}.backup"
                    os.rename(file_path, backup_path)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    
                    print(f"✅ 已保存修复后的文件")
                    print(f"📋 原文件备份为: {backup_path}")

if __name__ == "__main__":
    main()
