#!/bin/bash
# JaCoCo 功能验证工具
set -e

echo "🧪 JaCoCo 功能验证"
echo "=================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}💡 $1${NC}"; }

# 获取当前目录
CURRENT_DIR=$(pwd)
PROJECT_DIR="$CURRENT_DIR/quick_test_project"

# 清理旧项目
cleanup_old() {
    if [[ -d "$PROJECT_DIR" ]]; then
        rm -rf "$PROJECT_DIR"
    fi
}

# 创建简单测试项目
create_test_project() {
    print_info "创建测试项目..."
    
    cleanup_old
    mkdir -p "$PROJECT_DIR/src/main/java/com/test"
    mkdir -p "$PROJECT_DIR/src/test/java/com/test"
    
    # 创建主类
    cat > "$PROJECT_DIR/src/main/java/com/test/Calculator.java" << 'EOF'
package com.test;

public class Calculator {
    public int add(int a, int b) {
        System.out.println("Calculator.add called with: " + a + ", " + b);
        return a + b;
    }
    
    public int multiply(int a, int b) {
        System.out.println("Calculator.multiply called with: " + a + ", " + b);
        return a * b;
    }
}
EOF

    # 创建测试类
    cat > "$PROJECT_DIR/src/test/java/com/test/CalculatorTest.java" << 'EOF'
package com.test;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class CalculatorTest {
    
    @Test
    public void testAdd() {
        System.out.println("Running testAdd...");
        Calculator calc = new Calculator();
        int result = calc.add(2, 3);
        assertEquals(5, result);
        System.out.println("testAdd completed");
    }
    
    @Test
    public void testMultiply() {
        System.out.println("Running testMultiply...");
        Calculator calc = new Calculator();
        int result = calc.multiply(4, 5);
        assertEquals(20, result);
        System.out.println("testMultiply completed");
    }
}
EOF

    # 创建 pom.xml
    cat > "$PROJECT_DIR/pom.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.test</groupId>
    <artifactId>quick-test</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <junit.version>5.9.2</junit.version>
        <jacoco.version>0.8.8</jacoco.version>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>${junit.version}</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                </configuration>
            </plugin>
            
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.0.0-M9</version>
                <configuration>
                    <testFailureIgnore>true</testFailureIgnore>
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

    print_success "测试项目已创建: $PROJECT_DIR"
}

# 测试项目
test_project() {
    print_info "测试项目..."
    
    cd "$PROJECT_DIR"
    
    # 显示项目结构
    print_info "项目结构:"
    find . -type f -name "*.java" -o -name "pom.xml" | sort
    
    # 清理
    print_info "清理项目..."
    mvn clean -q
    
    # 编译主代码
    print_info "编译主代码..."
    if mvn compile -q; then
        print_success "主代码编译成功"
        
        # 检查编译结果
        if [[ -d "target/classes" ]]; then
            local class_count=$(find target/classes -name "*.class" | wc -l)
            print_info "编译生成 $class_count 个类文件"
        fi
    else
        print_error "主代码编译失败"
        return 1
    fi
    
    # 编译测试代码
    print_info "编译测试代码..."
    if mvn test-compile -q; then
        print_success "测试代码编译成功"
        
        # 检查编译结果
        if [[ -d "target/test-classes" ]]; then
            local test_class_count=$(find target/test-classes -name "*.class" | wc -l)
            print_info "编译生成 $test_class_count 个测试类文件"
        fi
    else
        print_error "测试代码编译失败"
        return 1
    fi
    
    # 运行测试（不使用 JaCoCo）
    print_info "运行测试（不使用 JaCoCo）..."
    mvn surefire:test -Dmaven.test.failure.ignore=true
    
    # 检查测试结果
    if [[ -d "target/surefire-reports" ]]; then
        print_success "测试执行完成"
        
        # 显示测试结果
        local xml_files=(target/surefire-reports/TEST-*.xml)
        for xml_file in "${xml_files[@]}"; do
            if [[ -f "$xml_file" ]]; then
                local tests=$(grep -o 'tests="[0-9]*"' "$xml_file" | cut -d'"' -f2)
                local failures=$(grep -o 'failures="[0-9]*"' "$xml_file" | cut -d'"' -f2)
                local errors=$(grep -o 'errors="[0-9]*"' "$xml_file" | cut -d'"' -f2)
                print_info "测试结果: $tests 个测试, $failures 个失败, $errors 个错误"
            fi
        done
    else
        print_warning "测试报告未生成"
    fi
    
    # 运行带 JaCoCo 的测试
    print_info "运行带 JaCoCo 的测试..."
    mvn clean test jacoco:report -Dmaven.test.failure.ignore=true
    
    # 检查 JaCoCo 结果
    check_jacoco_results
    
    cd "$CURRENT_DIR"
}

# 检查 JaCoCo 结果
check_jacoco_results() {
    print_info "检查 JaCoCo 结果..."
    
    # 检查执行数据文件
    if [[ -f "target/jacoco.exec" ]]; then
        local exec_size=$(stat -c%s "target/jacoco.exec" 2>/dev/null || echo "0")
        print_success "JaCoCo 执行数据文件存在，大小: $exec_size bytes"
        
        if [[ $exec_size -gt 0 ]]; then
            print_success "JaCoCo 收集到执行数据"
        else
            print_warning "JaCoCo 执行数据为空"
        fi
    else
        print_error "JaCoCo 执行数据文件不存在"
    fi
    
    # 检查 XML 报告
    if [[ -f "target/site/jacoco/jacoco.xml" ]]; then
        print_success "JaCoCo XML 报告已生成"
        
        # 显示报告内容
        print_info "JaCoCo 报告内容:"
        cat target/site/jacoco/jacoco.xml
        
        # 解析覆盖率
        local line_covered=$(grep -o 'type="LINE"[^>]*covered="[0-9]*"' "target/site/jacoco/jacoco.xml" | grep -o 'covered="[0-9]*"' | cut -d'"' -f2 | head -1)
        local line_missed=$(grep -o 'type="LINE"[^>]*missed="[0-9]*"' "target/site/jacoco/jacoco.xml" | grep -o 'missed="[0-9]*"' | cut -d'"' -f2 | head -1)
        
        if [[ -n "$line_covered" && -n "$line_missed" ]]; then
            local total=$((line_covered + line_missed))
            if [[ $total -gt 0 ]]; then
                local percentage=$(echo "scale=2; $line_covered * 100 / $total" | bc 2>/dev/null || echo "计算失败")
                print_success "🎉 覆盖率: $percentage% ($line_covered/$total 行)"
                
                if [[ $(echo "$percentage > 0" | bc 2>/dev/null) -eq 1 ]]; then
                    print_success "🎊 JaCoCo 基本功能正常！"
                    return 0
                fi
            fi
        fi
        
        print_warning "覆盖率为 0% 或解析失败"
    else
        print_error "JaCoCo XML 报告未生成"
    fi
    
    # 检查 HTML 报告
    if [[ -d "target/site/jacoco" ]]; then
        local html_count=$(find target/site/jacoco -name "*.html" | wc -l)
        if [[ $html_count -gt 0 ]]; then
            print_success "JaCoCo HTML 报告已生成: $html_count 个文件"
        fi
    fi
    
    return 1
}

# 清理函数
cleanup() {
    read -p "是否删除测试项目？(Y/n): " -r
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        cleanup_old
        print_info "测试项目已删除"
    else
        print_info "测试项目保留在: $PROJECT_DIR"
    fi
}

# 主函数
main() {
    print_info "开始快速 JaCoCo 功能测试..."
    
    # 检查基本环境
    if ! command -v mvn &> /dev/null; then
        print_error "Maven 未安装"
        exit 1
    fi
    
    if ! command -v java &> /dev/null; then
        print_error "Java 未安装"
        exit 1
    fi
    
    print_info "Maven 版本: $(mvn --version | head -1)"
    print_info "Java 版本: $(java -version 2>&1 | head -1)"
    
    # 创建和测试项目
    create_test_project
    
    if test_project; then
        print_success "🎉 JaCoCo 基本功能测试通过！"
        print_info "这说明 JaCoCo 环境是正常的，问题可能在真实项目的配置或代码结构上"
    else
        print_error "❌ JaCoCo 基本功能测试失败"
        print_info "这说明 JaCoCo 环境本身有问题，需要检查 Maven 和 Java 配置"
    fi
    
    cleanup
}

# 运行主函数
main "$@"
