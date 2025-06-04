#!/usr/bin/env python3
"""
Maven缓存预热脚本
预先下载常用的Maven依赖，避免每次扫描都重新下载
"""

import subprocess
import tempfile
import os
import shutil

def create_warmup_pom():
    """创建预热用的pom.xml"""
    pom_content = '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.warmup</groupId>
    <artifactId>maven-cache-warmup</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <jacoco.version>0.8.7</jacoco.version>
        <junit.version>4.13.2</junit.version>
    </properties>
    
    <dependencies>
        <!-- JUnit for testing -->
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>${junit.version}</version>
            <scope>test</scope>
        </dependency>
        
        <!-- MySQL Connector -->
        <dependency>
            <groupId>mysql</groupId>
            <artifactId>mysql-connector-java</artifactId>
            <version>8.0.33</version>
        </dependency>
    </dependencies>
    
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
                    <argLine>@{argLine}</argLine>
                </configuration>
            </plugin>
            
            <!-- JaCoCo Plugin -->
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>${jacoco.version}</version>
                <executions>
                    <execution>
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
    return pom_content

def create_dummy_java_files(temp_dir):
    """创建虚拟的Java文件"""
    # 创建主代码
    main_dir = os.path.join(temp_dir, "src", "main", "java", "com", "warmup")
    os.makedirs(main_dir, exist_ok=True)
    
    main_java = os.path.join(main_dir, "Main.java")
    with open(main_java, 'w') as f:
        f.write('''package com.warmup;

public class Main {
    public static void main(String[] args) {
        System.out.println("Maven cache warmup");
    }
    
    public int add(int a, int b) {
        return a + b;
    }
}''')
    
    # 创建测试代码
    test_dir = os.path.join(temp_dir, "src", "test", "java", "com", "warmup")
    os.makedirs(test_dir, exist_ok=True)
    
    test_java = os.path.join(test_dir, "MainTest.java")
    with open(test_java, 'w') as f:
        f.write('''package com.warmup;

import org.junit.Test;
import static org.junit.Assert.*;

public class MainTest {
    @Test
    public void testAdd() {
        Main main = new Main();
        assertEquals(5, main.add(2, 3));
    }
}''')

def warmup_maven_cache():
    """预热Maven缓存"""
    print("🔥 开始Maven缓存预热...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="maven_warmup_")
    print(f"临时目录: {temp_dir}")
    
    try:
        # 创建pom.xml
        pom_path = os.path.join(temp_dir, "pom.xml")
        with open(pom_path, 'w') as f:
            f.write(create_warmup_pom())
        print("✅ 创建预热pom.xml")
        
        # 创建虚拟Java文件
        create_dummy_java_files(temp_dir)
        print("✅ 创建虚拟Java文件")
        
        # 执行Maven命令下载依赖
        print("📦 下载Maven依赖...")
        commands = [
            ["mvn", "dependency:resolve"],
            ["mvn", "dependency:resolve-sources"],
            ["mvn", "clean", "compile"],
            ["mvn", "test-compile"],
            ["mvn", "test", "-Dmaven.test.failure.ignore=true"],
            ["mvn", "jacoco:report"]
        ]
        
        for i, cmd in enumerate(commands, 1):
            print(f"执行命令 {i}/{len(commands)}: {' '.join(cmd)}")
            try:
                result = subprocess.run(
                    cmd,
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    print(f"✅ 命令 {i} 执行成功")
                else:
                    print(f"⚠️ 命令 {i} 执行失败，但继续...")
                    
            except subprocess.TimeoutExpired:
                print(f"⚠️ 命令 {i} 超时，但继续...")
            except Exception as e:
                print(f"⚠️ 命令 {i} 异常: {e}")
        
        print("🎉 Maven缓存预热完成！")
        
        # 显示缓存信息
        maven_repo = os.path.expanduser("~/.m2/repository")
        if os.path.exists(maven_repo):
            print(f"📁 Maven本地仓库: {maven_repo}")
            
            # 检查关键依赖
            key_deps = [
                "org/jacoco",
                "junit/junit",
                "mysql/mysql-connector-java",
                "org/apache/maven/plugins"
            ]
            
            for dep in key_deps:
                dep_path = os.path.join(maven_repo, dep)
                if os.path.exists(dep_path):
                    print(f"✅ {dep}: 已缓存")
                else:
                    print(f"❌ {dep}: 未找到")
        
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
            print(f"🧹 清理临时目录: {temp_dir}")
        except Exception as e:
            print(f"⚠️ 清理临时目录失败: {e}")

def check_maven_cache():
    """检查Maven缓存状态"""
    print("🔍 检查Maven缓存状态")
    
    maven_repo = os.path.expanduser("~/.m2/repository")
    if not os.path.exists(maven_repo):
        print("❌ Maven本地仓库不存在")
        return False
    
    print(f"📁 Maven本地仓库: {maven_repo}")
    
    # 检查仓库大小
    try:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(maven_repo):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        
        size_mb = total_size / (1024 * 1024)
        print(f"📊 仓库大小: {size_mb:.1f} MB")
        
        if size_mb > 50:
            print("✅ Maven缓存充足")
            return True
        else:
            print("⚠️ Maven缓存较少，建议预热")
            return False
            
    except Exception as e:
        print(f"❌ 检查缓存大小失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Maven缓存管理工具")
    print("=" * 50)
    
    # 检查当前缓存状态
    cache_ok = check_maven_cache()
    
    if not cache_ok:
        print("\n需要预热Maven缓存...")
        warmup_maven_cache()
    else:
        print("\n✅ Maven缓存状态良好")
    
    print("\n💡 使用建议:")
    print("1. 首次使用前运行此脚本预热缓存")
    print("2. 定期运行以更新依赖")
    print("3. 如果扫描速度慢，重新运行此脚本")
    
    print("\n🔧 优化Maven扫描:")
    print("- 使用 -o 参数启用离线模式")
    print("- 使用 --batch-mode 减少输出")
    print("- 设置合理的超时时间")

if __name__ == "__main__":
    main()
