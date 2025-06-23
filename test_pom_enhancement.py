#!/usr/bin/env python3
"""测试 pom.xml 增强功能"""

import os
import tempfile
import shutil
import subprocess
from src.jacoco_tasks import enhance_pom_simple

def test_pom_enhancement():
    """测试 pom.xml 增强功能"""
    
    print("🧪 测试 pom.xml 增强功能")
    print("=" * 40)
    
    # 创建临时目录
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
            print("✅ 克隆成功")
        except Exception as e:
            print(f"❌ 克隆异常: {e}")
            return False
        
        # 检查原始 pom.xml
        pom_path = os.path.join(temp_dir, "pom.xml")
        if not os.path.exists(pom_path):
            print("❌ 未找到 pom.xml 文件")
            return False
        
        print("📄 检查原始 pom.xml...")
        with open(pom_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        print(f"📊 原始文件大小: {len(original_content)} 字符")
        
        # 检查是否包含 JaCoCo
        has_jacoco_before = 'jacoco' in original_content.lower()
        print(f"🔍 原始文件包含 JaCoCo: {has_jacoco_before}")
        
        # 备份原始文件
        backup_path = pom_path + ".backup"
        shutil.copy2(pom_path, backup_path)
        print("💾 已备份原始文件")
        
        # 增强 pom.xml
        print("🔧 增强 pom.xml...")
        try:
            enhance_pom_simple(pom_path, "test_request")
            print("✅ 增强完成")
        except Exception as e:
            print(f"❌ 增强失败: {e}")
            return False
        
        # 检查增强后的 pom.xml
        print("📄 检查增强后的 pom.xml...")
        with open(pom_path, 'r', encoding='utf-8') as f:
            enhanced_content = f.read()
        
        print(f"📊 增强后文件大小: {len(enhanced_content)} 字符")
        
        # 检查是否包含 JaCoCo
        has_jacoco_after = 'jacoco' in enhanced_content.lower()
        print(f"🔍 增强后文件包含 JaCoCo: {has_jacoco_after}")
        
        # 检查具体的 JaCoCo 配置
        jacoco_plugin = 'jacoco-maven-plugin' in enhanced_content
        jacoco_version = '${jacoco.version}' in enhanced_content
        jacoco_executions = 'prepare-agent' in enhanced_content and 'report' in enhanced_content
        
        print(f"🔍 JaCoCo 插件: {jacoco_plugin}")
        print(f"🔍 JaCoCo 版本变量: {jacoco_version}")
        print(f"🔍 JaCoCo 执行配置: {jacoco_executions}")
        
        # 测试 Maven 验证
        print("\n🔨 测试 Maven 验证...")
        os.chdir(temp_dir)
        
        # 验证 pom.xml 语法
        validate_cmd = ["mvn", "validate", "-B", "-q"]
        try:
            result = subprocess.run(validate_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("✅ Maven 验证通过")
            else:
                print(f"❌ Maven 验证失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"⚠️  Maven 验证异常: {e}")
        
        # 测试 JaCoCo 插件是否可用
        print("🔍 测试 JaCoCo 插件...")
        jacoco_cmd = ["mvn", "jacoco:help", "-B", "-q"]
        try:
            result = subprocess.run(jacoco_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("✅ JaCoCo 插件可用")
                jacoco_available = True
            else:
                print(f"❌ JaCoCo 插件不可用: {result.stderr}")
                jacoco_available = False
        except Exception as e:
            print(f"⚠️  JaCoCo 插件测试异常: {e}")
            jacoco_available = False
        
        # 显示差异
        if len(enhanced_content) > len(original_content):
            added_lines = enhanced_content.count('\n') - original_content.count('\n')
            print(f"📈 增加了 {added_lines} 行")
        
        # 总结
        print("\n" + "=" * 40)
        print("📊 测试结果总结:")
        print(f"✅ 文件增强: {'成功' if has_jacoco_after else '失败'}")
        print(f"✅ JaCoCo 插件: {'已添加' if jacoco_plugin else '未添加'}")
        print(f"✅ Maven 验证: {'通过' if result.returncode == 0 else '失败'}")
        print(f"✅ JaCoCo 可用: {'是' if jacoco_available else '否'}")
        
        success = has_jacoco_after and jacoco_plugin and jacoco_available
        
        if success:
            print("🎉 pom.xml 增强功能正常工作！")
        else:
            print("❌ pom.xml 增强功能有问题")
            
            # 显示增强后的内容片段
            print("\n📄 增强后的 pom.xml 片段:")
            lines = enhanced_content.split('\n')
            for i, line in enumerate(lines):
                if 'jacoco' in line.lower():
                    start = max(0, i-2)
                    end = min(len(lines), i+3)
                    for j in range(start, end):
                        marker = ">>> " if j == i else "    "
                        print(f"{marker}{j+1:3d}: {lines[j]}")
                    break
        
        return success

def main():
    """主函数"""
    
    print("🔧 JaCoCo pom.xml 增强功能测试")
    print("=" * 50)
    
    success = test_pom_enhancement()
    
    if success:
        print("\n🎉 所有测试通过！pom.xml 增强功能正常。")
    else:
        print("\n❌ 测试失败！需要检查 pom.xml 增强功能。")
    
    return success

if __name__ == "__main__":
    main()
