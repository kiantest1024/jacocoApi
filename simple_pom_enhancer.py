#!/usr/bin/env python3
"""
简单的pom.xml增强器 - 使用字符串替换避免XML解析问题
"""

import os
import re

def enhance_pom_simple(pom_path: str) -> bool:
    """
    使用字符串替换简单增强pom.xml
    """
    try:
        # 读取pom.xml
        with open(pom_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📋 原始pom.xml大小: {len(content)} 字符")
        
        # 检查是否已有JaCoCo插件
        if 'jacoco-maven-plugin' in content:
            print("✅ JaCoCo插件已存在，跳过增强")
            return True
        
        # 添加JaCoCo属性
        jacoco_property = '<jacoco.version>0.8.7</jacoco.version>'
        
        if '<properties>' in content and jacoco_property not in content:
            # 在现有properties中添加
            content = content.replace(
                '<properties>',
                f'<properties>\n        {jacoco_property}'
            )
            print("✅ 在现有properties中添加JaCoCo版本")
        elif '<properties>' not in content:
            # 创建properties节点
            # 在</version>后添加properties
            version_pattern = r'(\s*</version>\s*)'
            if re.search(version_pattern, content):
                properties_block = f'''
    <properties>
        {jacoco_property}
    </properties>'''
                content = re.sub(version_pattern, r'\1' + properties_block, content, count=1)
                print("✅ 创建properties节点并添加JaCoCo版本")
        
        # 添加JaCoCo插件
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
        
        if '<plugins>' in content:
            # 在现有plugins中添加
            content = content.replace(
                '<plugins>',
                f'<plugins>{jacoco_plugin}'
            )
            print("✅ 在现有plugins中添加JaCoCo插件")
        elif '<build>' in content:
            # 在build中创建plugins
            plugins_block = f'''
        <plugins>{jacoco_plugin}
        </plugins>'''
            content = content.replace(
                '<build>',
                f'<build>{plugins_block}'
            )
            print("✅ 在build中创建plugins并添加JaCoCo插件")
        else:
            # 创建完整的build节点
            build_block = f'''
    <build>
        <plugins>{jacoco_plugin}
        </plugins>
    </build>'''
            # 在</dependencies>后或</properties>后添加
            if '</dependencies>' in content:
                content = content.replace('</dependencies>', f'</dependencies>{build_block}')
            elif '</properties>' in content:
                content = content.replace('</properties>', f'</properties>{build_block}')
            else:
                # 在</project>前添加
                content = content.replace('</project>', f'{build_block}\n</project>')
            print("✅ 创建完整的build节点并添加JaCoCo插件")
        
        # 写回文件
        with open(pom_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ pom.xml增强完成，新大小: {len(content)} 字符")
        return True
        
    except Exception as e:
        print(f"❌ pom.xml增强失败: {e}")
        return False

def test_enhance():
    """测试增强功能"""
    # 创建测试pom.xml
    test_pom = '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <dependencies>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
    
</project>'''
    
    # 写入测试文件
    test_file = 'test_pom.xml'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_pom)
    
    print("🧪 测试pom.xml增强功能")
    print("=" * 40)
    
    # 增强
    result = enhance_pom_simple(test_file)
    
    if result:
        print("\n📄 增强后的pom.xml:")
        with open(test_file, 'r', encoding='utf-8') as f:
            enhanced_content = f.read()
        print(enhanced_content)
    
    # 清理
    try:
        os.remove(test_file)
    except:
        pass
    
    return result

if __name__ == "__main__":
    test_enhance()
