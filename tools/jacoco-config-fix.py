#!/usr/bin/env python3
"""
JaCoCo 配置修复工具
专门解决 JaCoCo 报告生成问题
"""

import os
import re
import tempfile
import subprocess
import shutil

def analyze_jacoco_issues(pom_path):
    """分析 JaCoCo 配置问题"""
    
    print("🔍 分析 JaCoCo 配置问题...")
    
    if not os.path.exists(pom_path):
        print(f"❌ pom.xml 文件不存在: {pom_path}")
        return []
    
    with open(pom_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # 1. 检查 JaCoCo 版本
    jacoco_version_pattern = r'<jacoco\.version>(.*?)</jacoco\.version>'
    version_match = re.search(jacoco_version_pattern, content)
    
    if not version_match:
        issues.append({
            'type': 'missing_version',
            'severity': 'error',
            'message': '缺少 JaCoCo 版本属性',
            'fix': '添加 <jacoco.version>0.8.8</jacoco.version>'
        })
    else:
        version = version_match.group(1)
        print(f"📋 JaCoCo 版本: {version}")
        
        # 检查版本是否过旧
        if version.startswith('0.7') or version.startswith('0.6'):
            issues.append({
                'type': 'old_version',
                'severity': 'warning',
                'message': f'JaCoCo 版本过旧: {version}',
                'fix': '建议升级到 0.8.8 或更新版本'
            })
    
    # 2. 检查 JaCoCo 插件配置
    jacoco_plugin_pattern = r'<groupId>org\.jacoco</groupId>\s*<artifactId>jacoco-maven-plugin</artifactId>'
    if not re.search(jacoco_plugin_pattern, content):
        issues.append({
            'type': 'missing_plugin',
            'severity': 'error',
            'message': '缺少 JaCoCo Maven 插件',
            'fix': '添加 jacoco-maven-plugin 插件配置'
        })
    
    # 3. 检查 prepare-agent 配置
    if 'prepare-agent' not in content:
        issues.append({
            'type': 'missing_prepare_agent',
            'severity': 'error',
            'message': '缺少 prepare-agent 目标',
            'fix': '添加 prepare-agent 执行配置'
        })
    
    # 4. 检查 report 配置
    if '<goal>report</goal>' not in content:
        issues.append({
            'type': 'missing_report_goal',
            'severity': 'error',
            'message': '缺少 report 目标',
            'fix': '添加 report 执行配置'
        })
    
    # 5. 检查 Surefire 插件版本
    surefire_pattern = r'<artifactId>maven-surefire-plugin</artifactId>\s*<version>(.*?)</version>'
    surefire_match = re.search(surefire_pattern, content)
    
    if surefire_match:
        surefire_version = surefire_match.group(1)
        print(f"📋 Surefire 版本: {surefire_version}")
        
        # 检查是否是过旧版本
        if surefire_version.startswith('2.12') or surefire_version.startswith('2.11'):
            issues.append({
                'type': 'old_surefire',
                'severity': 'warning',
                'message': f'Surefire 版本过旧: {surefire_version}',
                'fix': '建议升级到 3.0.0-M9 或更新版本'
            })
    
    # 6. 检查 JUnit 版本兼容性
    junit5_pattern = r'<groupId>org\.junit\.jupiter</groupId>'
    junit4_pattern = r'<groupId>junit</groupId>\s*<artifactId>junit</artifactId>'
    
    has_junit5 = re.search(junit5_pattern, content)
    has_junit4 = re.search(junit4_pattern, content)
    
    if has_junit5 and has_junit4:
        issues.append({
            'type': 'mixed_junit',
            'severity': 'warning',
            'message': '同时使用 JUnit 4 和 JUnit 5',
            'fix': '建议统一使用 JUnit 5'
        })
    
    return issues

def generate_enhanced_pom_config():
    """生成增强的 JaCoCo 配置"""
    
    return '''
    <!-- JaCoCo 增强配置 -->
    <properties>
        <jacoco.version>0.8.8</jacoco.version>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <junit.version>5.9.2</junit.version>
    </properties>
    
    <build>
        <plugins>
            <!-- Maven Compiler Plugin -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                    <encoding>UTF-8</encoding>
                </configuration>
            </plugin>
            
            <!-- Maven Surefire Plugin -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.0.0-M9</version>
                <configuration>
                    <testFailureIgnore>true</testFailureIgnore>
                    <argLine>${argLine}</argLine>
                </configuration>
            </plugin>
            
            <!-- JaCoCo Plugin - 增强配置 -->
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>${jacoco.version}</version>
                <executions>
                    <!-- 准备代理 -->
                    <execution>
                        <id>prepare-agent</id>
                        <goals>
                            <goal>prepare-agent</goal>
                        </goals>
                        <configuration>
                            <propertyName>argLine</propertyName>
                        </configuration>
                    </execution>
                    
                    <!-- 生成报告 -->
                    <execution>
                        <id>report</id>
                        <phase>test</phase>
                        <goals>
                            <goal>report</goal>
                        </goals>
                        <configuration>
                            <outputDirectory>${project.reporting.outputDirectory}/jacoco</outputDirectory>
                        </configuration>
                    </execution>
                    
                    <!-- 验证覆盖率 -->
                    <execution>
                        <id>check</id>
                        <goals>
                            <goal>check</goal>
                        </goals>
                        <configuration>
                            <rules>
                                <rule>
                                    <element>BUNDLE</element>
                                    <limits>
                                        <limit>
                                            <counter>INSTRUCTION</counter>
                                            <value>COVEREDRATIO</value>
                                            <minimum>0.00</minimum>
                                        </limit>
                                    </limits>
                                </rule>
                            </rules>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
    
    <reporting>
        <plugins>
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>${jacoco.version}</version>
                <reportSets>
                    <reportSet>
                        <reports>
                            <report>report</report>
                        </reports>
                    </reportSet>
                </reportSets>
            </plugin>
        </plugins>
    </reporting>
'''

def fix_jacoco_configuration(pom_path):
    """修复 JaCoCo 配置"""
    
    print(f"🔧 修复 JaCoCo 配置: {pom_path}")
    
    # 分析问题
    issues = analyze_jacoco_issues(pom_path)
    
    if not issues:
        print("✅ JaCoCo 配置看起来正常")
        return True
    
    print(f"🔍 发现 {len(issues)} 个问题:")
    for issue in issues:
        severity_icon = "🔴" if issue['severity'] == 'error' else "🟡"
        print(f"{severity_icon} {issue['message']}")
        print(f"   💡 修复: {issue['fix']}")
    
    # 备份原文件
    backup_path = pom_path + ".jacoco_backup"
    shutil.copy2(pom_path, backup_path)
    print(f"💾 已备份原文件: {backup_path}")
    
    # 读取原文件
    with open(pom_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 应用修复
    fixed_content = content
    
    # 修复 JaCoCo 版本
    if not re.search(r'<jacoco\.version>', content):
        # 在 properties 中添加版本
        if '<properties>' in content:
            fixed_content = re.sub(
                r'(<properties>\s*)',
                r'\1<jacoco.version>0.8.8</jacoco.version>\n        ',
                fixed_content
            )
        else:
            # 添加 properties 部分
            fixed_content = re.sub(
                r'(<modelVersion>.*?</modelVersion>)',
                r'\1\n\n    <properties>\n        <jacoco.version>0.8.8</jacoco.version>\n        <maven.compiler.source>11</maven.compiler.source>\n        <maven.compiler.target>11</maven.compiler.target>\n        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>\n    </properties>',
                fixed_content
            )
    
    # 修复 Surefire 插件配置
    if 'argLine>${argLine}' not in content:
        # 添加 argLine 配置到 Surefire 插件
        surefire_config_pattern = r'(<plugin>\s*<groupId>org\.apache\.maven\.plugins</groupId>\s*<artifactId>maven-surefire-plugin</artifactId>.*?<configuration>)(.*?)(</configuration>)'
        
        def add_argline(match):
            start = match.group(1)
            config = match.group(2)
            end = match.group(3)
            
            if 'argLine' not in config:
                config += '\n                    <argLine>${argLine}</argLine>'
            
            return start + config + end
        
        fixed_content = re.sub(surefire_config_pattern, add_argline, fixed_content, flags=re.DOTALL)
    
    # 保存修复后的文件
    with open(pom_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("✅ JaCoCo 配置修复完成")
    
    # 验证修复
    print("🔍 验证修复结果...")
    new_issues = analyze_jacoco_issues(pom_path)
    
    if len(new_issues) < len(issues):
        print(f"✅ 修复成功，问题数量从 {len(issues)} 减少到 {len(new_issues)}")
    else:
        print("⚠️  修复可能不完整，请手动检查")
    
    return len(new_issues) == 0

def test_jacoco_with_simple_project():
    """使用简单项目测试 JaCoCo"""
    
    print("🧪 使用简单项目测试 JaCoCo...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 临时目录: {temp_dir}")
        
        # 克隆测试项目
        print("📥 克隆测试项目...")
        clone_cmd = [
            "git", "clone", "--depth", "1", "--branch", "main",
            "http://172.16.1.30/kian/jacocotest.git",
            temp_dir
        ]
        
        try:
            result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"❌ 克隆失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 克隆异常: {e}")
            return False
        
        pom_path = os.path.join(temp_dir, "pom.xml")
        
        # 修复配置
        fix_jacoco_configuration(pom_path)
        
        # 切换到项目目录
        os.chdir(temp_dir)
        
        # 运行测试
        print("🔨 运行 Maven 测试...")
        test_cmd = ["mvn", "clean", "test", "-B", "-e"]
        
        try:
            result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=120)
            print(f"📊 Maven 测试返回码: {result.returncode}")
            
            if result.returncode == 0:
                print("✅ Maven 测试成功")
            else:
                print("⚠️  Maven 测试有问题，但继续检查 JaCoCo")
            
            # 检查 JaCoCo 执行数据
            exec_file = "target/jacoco.exec"
            if os.path.exists(exec_file):
                size = os.path.getsize(exec_file)
                print(f"✅ JaCoCo 执行数据文件存在: {size} bytes")
            else:
                print("❌ JaCoCo 执行数据文件不存在")
            
            # 运行 JaCoCo 报告
            print("📊 生成 JaCoCo 报告...")
            report_cmd = ["mvn", "jacoco:report", "-B", "-e"]
            
            result = subprocess.run(report_cmd, capture_output=True, text=True, timeout=60)
            print(f"📊 JaCoCo 报告返回码: {result.returncode}")
            
            if result.returncode == 0:
                print("✅ JaCoCo 报告生成成功")
            else:
                print(f"❌ JaCoCo 报告生成失败: {result.stderr}")
            
            # 检查报告文件
            report_locations = [
                "target/site/jacoco/jacoco.xml",
                "target/jacoco-reports/jacoco.xml",
                "target/reports/jacoco/jacoco.xml"
            ]
            
            found_report = False
            for location in report_locations:
                if os.path.exists(location):
                    size = os.path.getsize(location)
                    print(f"✅ 找到 JaCoCo 报告: {location} ({size} bytes)")
                    found_report = True
                    break
            
            if not found_report:
                print("❌ 未找到 JaCoCo XML 报告")
                
                # 显示 target 目录结构
                print("📁 target 目录结构:")
                for root, dirs, files in os.walk("target"):
                    level = root.replace("target", "").count(os.sep)
                    indent = " " * 2 * level
                    print(f"{indent}{os.path.basename(root)}/")
                    subindent = " " * 2 * (level + 1)
                    for file in files:
                        print(f"{subindent}{file}")
            
            return found_report
            
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False

def main():
    """主函数"""
    
    print("🔧 JaCoCo 配置修复工具")
    print("=" * 40)
    
    print("选择操作:")
    print("1. 分析现有项目的 JaCoCo 配置")
    print("2. 使用测试项目验证 JaCoCo")
    print("3. 显示增强配置模板")
    
    choice = input("\n请选择 (1-3): ").strip()
    
    if choice == "1":
        pom_path = input("请输入 pom.xml 文件路径: ").strip()
        if os.path.exists(pom_path):
            fix_jacoco_configuration(pom_path)
        else:
            print(f"❌ 文件不存在: {pom_path}")
    
    elif choice == "2":
        test_jacoco_with_simple_project()
    
    elif choice == "3":
        print("📄 JaCoCo 增强配置模板:")
        print(generate_enhanced_pom_config())
    
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()
