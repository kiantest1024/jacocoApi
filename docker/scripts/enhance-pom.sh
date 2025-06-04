#!/bin/bash

# 增强pom.xml以支持JaCoCo
set -e

POM_FILE="pom.xml"

if [[ ! -f "$POM_FILE" ]]; then
    echo "错误: 未找到pom.xml文件"
    exit 1
fi

echo "备份原始pom.xml..."
cp "$POM_FILE" "${POM_FILE}.backup"

echo "增强pom.xml以支持JaCoCo..."

# 创建临时的JaCoCo配置
cat > jacoco-plugin.xml << 'EOF'
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>0.8.7</version>
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
            </plugin>
EOF

# 使用Python脚本来安全地修改XML
python3 << 'EOF'
import xml.etree.ElementTree as ET
import sys

try:
    # 解析pom.xml
    tree = ET.parse('pom.xml')
    root = tree.getroot()
    
    # 获取命名空间
    namespace = ''
    if root.tag.startswith('{'):
        namespace = root.tag[1:root.tag.index('}')]
        ET.register_namespace('', namespace)
    
    # 查找或创建properties
    properties = root.find('.//{http://maven.apache.org/POM/4.0.0}properties' if namespace else './/properties')
    if properties is None:
        properties = ET.SubElement(root, 'properties')
    
    # 添加JaCoCo版本属性
    jacoco_version = properties.find('.//{http://maven.apache.org/POM/4.0.0}jacoco.version' if namespace else './/jacoco.version')
    if jacoco_version is None:
        jacoco_version = ET.SubElement(properties, 'jacoco.version')
        jacoco_version.text = '0.8.7'
    
    # 查找或创建build
    build = root.find('.//{http://maven.apache.org/POM/4.0.0}build' if namespace else './/build')
    if build is None:
        build = ET.SubElement(root, 'build')
    
    # 查找或创建plugins
    plugins = build.find('.//{http://maven.apache.org/POM/4.0.0}plugins' if namespace else './/plugins')
    if plugins is None:
        plugins = ET.SubElement(build, 'plugins')
    
    # 检查是否已有JaCoCo插件
    jacoco_exists = False
    for plugin in plugins.findall('.//{http://maven.apache.org/POM/4.0.0}plugin' if namespace else './/plugin'):
        artifact_id = plugin.find('.//{http://maven.apache.org/POM/4.0.0}artifactId' if namespace else './/artifactId')
        if artifact_id is not None and artifact_id.text == 'jacoco-maven-plugin':
            jacoco_exists = True
            break
    
    if not jacoco_exists:
        # 读取JaCoCo插件配置
        with open('jacoco-plugin.xml', 'r') as f:
            plugin_xml = f.read()
        
        # 解析插件配置并添加到plugins
        plugin_element = ET.fromstring('<plugin>' + plugin_xml.split('<plugin>')[1].split('</plugin>')[0] + '</plugin>')
        plugins.append(plugin_element)
    
    # 写回文件
    tree.write('pom.xml', encoding='utf-8', xml_declaration=True)
    print("pom.xml增强完成")
    
except Exception as e:
    print(f"增强pom.xml失败: {e}")
    sys.exit(1)
EOF

# 清理临时文件
rm -f jacoco-plugin.xml

echo "pom.xml增强完成"
