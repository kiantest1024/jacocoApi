#!/bin/bash

echo "🔍 深度诊断JaCoCo覆盖率问题..."

# 创建诊断目录
DIAG_DIR="/tmp/jacoco_diagnosis_$(date +%s)"
mkdir -p "$DIAG_DIR"
cd "$DIAG_DIR"

echo "📁 诊断目录: $DIAG_DIR"

# 克隆项目
echo "📥 克隆项目..."
git clone http://172.16.1.30/kian/jacocotest.git
cd jacocotest

# 检查项目结构
echo "📂 项目结构:"
find . -name "*.java" -o -name "pom.xml" -o -name "*.xml" | head -20

# 检查原始pom.xml
echo "📄 原始pom.xml内容:"
cat pom.xml

# 检查是否有测试文件
echo "🧪 测试文件:"
find . -path "*/test/*" -name "*.java" | head -10

# 检查源代码文件
echo "💻 源代码文件:"
find . -path "*/main/*" -name "*.java" | head -10

# 尝试原始Maven命令
echo "🔨 测试原始Maven命令..."
mvn clean test -Dmaven.test.failure.ignore=true --batch-mode

# 检查是否生成了任何测试报告
echo "📊 检查测试报告:"
find . -name "TEST-*.xml" -o -name "*.exec" -o -name "jacoco*" | head -10

# 手动添加JaCoCo插件
echo "🔧 手动添加JaCoCo插件..."
cp pom.xml pom.xml.backup

# 创建增强的pom.xml
cat > pom_enhanced.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
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
        <jacoco.version>0.8.8</jacoco.version>
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
                    <includes>
                        <include>**/*Test.java</include>
                        <include>**/*Tests.java</include>
                    </includes>
                </configuration>
            </plugin>
            
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
            </plugin>
        </plugins>
    </build>
</project>
EOF

# 使用增强的pom.xml
cp pom_enhanced.xml pom.xml

echo "📄 增强后的pom.xml:"
cat pom.xml

# 重新运行Maven
echo "🚀 使用增强pom.xml运行Maven..."
mvn clean compile test jacoco:report -Dmaven.test.failure.ignore=true --batch-mode -X

# 检查生成的文件
echo "📁 生成的文件:"
find . -name "*.exec" -o -name "jacoco.xml" -o -name "*.html" | head -20

# 检查target目录结构
echo "📂 target目录结构:"
if [ -d "target" ]; then
    find target -type f | head -30
fi

# 如果找到jacoco.xml，显示内容
JACOCO_XML=$(find . -name "jacoco.xml" | head -1)
if [ -n "$JACOCO_XML" ]; then
    echo "📄 JaCoCo XML内容:"
    cat "$JACOCO_XML"
else
    echo "❌ 未找到jacoco.xml文件"
fi

# 检查jacoco.exec文件
JACOCO_EXEC=$(find . -name "jacoco.exec" | head -1)
if [ -n "$JACOCO_EXEC" ]; then
    echo "📊 JaCoCo exec文件信息:"
    ls -la "$JACOCO_EXEC"
    echo "文件大小: $(wc -c < "$JACOCO_EXEC") bytes"
else
    echo "❌ 未找到jacoco.exec文件"
fi

echo "✅ 诊断完成，结果保存在: $DIAG_DIR"
