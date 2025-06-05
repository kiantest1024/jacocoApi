#!/usr/bin/env python3

import subprocess
import tempfile
import os
import xml.etree.ElementTree as ET

def test_local_jacoco():
    print("🧪 本地测试JaCoCo...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 临时目录: {temp_dir}")
        
        # 克隆项目
        print("📥 克隆项目...")
        project_dir = os.path.join(temp_dir, "jacocotest")
        
        try:
            subprocess.run([
                "git", "clone", 
                "http://172.16.1.30/kian/jacocotest.git",
                project_dir
            ], check=True, timeout=60)
        except Exception as e:
            print(f"❌ 克隆失败: {e}")
            return False
        
        os.chdir(project_dir)
        
        # 创建标准的JaCoCo pom.xml
        pom_content = '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>jacocotest</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.8.1</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                </configuration>
            </plugin>
            
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.0.0-M7</version>
                <configuration>
                    <argLine>${argLine}</argLine>
                </configuration>
            </plugin>
            
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>0.8.8</version>
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
        </plugins>
    </build>
</project>'''
        
        # 写入新的pom.xml
        with open("pom.xml", "w", encoding="utf-8") as f:
            f.write(pom_content)
        
        print("📄 已创建标准pom.xml")
        
        # 运行Maven
        print("🔨 运行Maven测试...")
        try:
            result = subprocess.run([
                "mvn", "clean", "test", "jacoco:report",
                "-Dmaven.test.failure.ignore=true",
                "--batch-mode"
            ], capture_output=True, text=True, timeout=180)
            
            print(f"Maven返回码: {result.returncode}")
            if result.stdout:
                print("Maven输出:")
                print(result.stdout[-1000:])  # 最后1000字符
            if result.stderr:
                print("Maven错误:")
                print(result.stderr[-500:])   # 最后500字符
                
        except Exception as e:
            print(f"❌ Maven执行失败: {e}")
            return False
        
        # 查找JaCoCo报告
        jacoco_xml = None
        for root, dirs, files in os.walk("."):
            for file in files:
                if file == "jacoco.xml":
                    jacoco_xml = os.path.join(root, file)
                    break
            if jacoco_xml:
                break
        
        if jacoco_xml:
            print(f"✅ 找到JaCoCo报告: {jacoco_xml}")
            
            # 解析XML内容
            try:
                with open(jacoco_xml, "r", encoding="utf-8") as f:
                    content = f.read()
                
                print(f"📄 XML文件大小: {len(content)} 字符")
                print("📄 XML内容:")
                print(content)
                
                # 解析覆盖率数据
                root = ET.fromstring(content)
                
                total_instructions = 0
                covered_instructions = 0
                
                for counter in root.findall(".//counter[@type='INSTRUCTION']"):
                    missed = int(counter.get('missed', 0))
                    covered = int(counter.get('covered', 0))
                    total_instructions += missed + covered
                    covered_instructions += covered
                
                if total_instructions > 0:
                    coverage_percent = (covered_instructions / total_instructions) * 100
                    print(f"✅ 指令覆盖率: {coverage_percent:.2f}% ({covered_instructions}/{total_instructions})")
                    return True
                else:
                    print("❌ 没有找到覆盖率数据")
                    return False
                    
            except Exception as e:
                print(f"❌ 解析XML失败: {e}")
                return False
        else:
            print("❌ 未找到JaCoCo报告")
            return False

def main():
    print("🔧 本地JaCoCo测试")
    print("=" * 50)
    
    if test_local_jacoco():
        print("\n🎉 本地测试成功！项目确实有覆盖率数据")
        print("问题可能在Docker环境或配置中")
    else:
        print("\n❌ 本地测试失败")
        print("问题可能在项目本身或Maven配置中")

if __name__ == "__main__":
    main()
