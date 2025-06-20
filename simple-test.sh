#!/bin/bash

# 简化的 JaCoCo 测试脚本
# 专注于验证基本的测试执行和覆盖率收集

set -e

echo "🧪 简化 JaCoCo 测试验证"
echo "======================"

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

# 创建一个最简单的测试项目
create_simple_project() {
    local project_dir="simple_test_project"
    
    print_info "创建简单测试项目..."
    
    rm -rf "$project_dir"
    mkdir -p "$project_dir/src/main/java/com/test"
    mkdir -p "$project_dir/src/test/java/com/test"
    
    # 创建简单的主类
    cat > "$project_dir/src/main/java/com/test/Calculator.java" << 'EOF'
package com.test;

public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    public int subtract(int a, int b) {
        return a - b;
    }
    
    public int multiply(int a, int b) {
        return a * b;
    }
}
EOF

    # 创建简单的测试类
    cat > "$project_dir/src/test/java/com/test/CalculatorTest.java" << 'EOF'
package com.test;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class CalculatorTest {
    
    @Test
    public void testAdd() {
        Calculator calc = new Calculator();
        assertEquals(5, calc.add(2, 3));
        assertEquals(0, calc.add(-1, 1));
    }
    
    @Test
    public void testSubtract() {
        Calculator calc = new Calculator();
        assertEquals(1, calc.subtract(3, 2));
        assertEquals(-2, calc.subtract(-1, 1));
    }
    
    @Test
    public void testMultiply() {
        Calculator calc = new Calculator();
        assertEquals(6, calc.multiply(2, 3));
        assertEquals(0, calc.multiply(0, 5));
    }
}
EOF

    # 创建 pom.xml
    cat > "$project_dir/pom.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.test</groupId>
    <artifactId>simple-test</artifactId>
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

    print_success "简单测试项目已创建: $project_dir"
    echo "$project_dir"
}

# 测试简单项目
test_simple_project() {
    local project_dir="$1"
    
    print_info "测试简单项目..."
    cd "$project_dir"
    
    # 清理
    print_info "清理项目..."
    mvn clean -q
    
    # 编译
    print_info "编译项目..."
    if mvn compile -q; then
        print_success "编译成功"
    else
        print_error "编译失败"
        return 1
    fi
    
    # 编译测试
    print_info "编译测试..."
    if mvn test-compile -q; then
        print_success "测试编译成功"
    else
        print_error "测试编译失败"
        return 1
    fi
    
    # 运行测试
    print_info "运行测试..."
    mvn test -q
    
    # 检查测试结果
    if [[ -d "target/surefire-reports" ]]; then
        print_success "测试报告已生成"
        ls -la target/surefire-reports/
        
        # 统计测试结果
        local test_files=(target/surefire-reports/TEST-*.xml)
        for test_file in "${test_files[@]}"; do
            if [[ -f "$test_file" ]]; then
                local tests=$(grep -o 'tests="[0-9]*"' "$test_file" | cut -d'"' -f2)
                local failures=$(grep -o 'failures="[0-9]*"' "$test_file" | cut -d'"' -f2)
                local errors=$(grep -o 'errors="[0-9]*"' "$test_file" | cut -d'"' -f2)
                
                print_info "测试结果: $tests 个测试, $failures 个失败, $errors 个错误"
            fi
        done
    else
        print_warning "未生成测试报告"
    fi
    
    # 生成 JaCoCo 报告
    print_info "生成 JaCoCo 报告..."
    mvn jacoco:report -q
    
    # 检查 JaCoCo 结果
    if [[ -f "target/jacoco.exec" ]]; then
        local exec_size=$(stat -f%z "target/jacoco.exec" 2>/dev/null || stat -c%s "target/jacoco.exec" 2>/dev/null || echo "0")
        print_success "JaCoCo 执行数据: $exec_size bytes"
    else
        print_error "JaCoCo 执行数据不存在"
    fi
    
    if [[ -f "target/site/jacoco/jacoco.xml" ]]; then
        print_success "JaCoCo XML 报告已生成"
        
        # 解析覆盖率
        local line_covered=$(grep -o 'type="LINE"[^>]*covered="[0-9]*"' "target/site/jacoco/jacoco.xml" | grep -o 'covered="[0-9]*"' | cut -d'"' -f2 | head -1)
        local line_missed=$(grep -o 'type="LINE"[^>]*missed="[0-9]*"' "target/site/jacoco/jacoco.xml" | grep -o 'missed="[0-9]*"' | cut -d'"' -f2 | head -1)
        
        if [[ -n "$line_covered" && -n "$line_missed" ]]; then
            local total=$((line_covered + line_missed))
            if [[ $total -gt 0 ]]; then
                local percentage=$(echo "scale=2; $line_covered * 100 / $total" | bc 2>/dev/null || echo "计算失败")
                print_success "简单项目覆盖率: $percentage% ($line_covered/$total 行)"
                
                if [[ $(echo "$percentage > 0" | bc 2>/dev/null) -eq 1 ]]; then
                    print_success "🎉 基本 JaCoCo 功能正常！"
                    return 0
                fi
            fi
        fi
        
        print_warning "简单项目覆盖率为 0%"
    else
        print_error "JaCoCo XML 报告未生成"
    fi
    
    return 1
}

# 使用 Docker 测试简单项目
test_with_docker() {
    local project_dir="$1"
    
    print_info "使用 Docker 测试简单项目..."
    
    # 检查 Docker 镜像
    if ! docker images | grep -q "jacoco-scanner.*latest"; then
        print_error "jacoco-scanner 镜像不存在"
        return 1
    fi
    
    # 创建临时报告目录
    local reports_dir=$(mktemp -d)
    
    # 将简单项目推送到临时 Git 仓库（模拟）
    # 这里我们直接挂载项目目录
    print_info "运行 Docker 扫描..."
    
    # 由于我们的简单项目不在 Git 仓库中，我们需要修改测试方法
    # 直接在容器内运行测试
    if docker run --rm \
        -v "$(pwd)/$project_dir:/app/test_project" \
        -v "$reports_dir:/app/reports" \
        -w /app/test_project \
        jacoco-scanner:latest \
        bash -c "
            echo '测试 Docker 内的 Maven 环境...'
            mvn clean test jacoco:report -Dmaven.test.failure.ignore=true
            
            # 复制报告
            if [[ -f target/site/jacoco/jacoco.xml ]]; then
                cp target/site/jacoco/jacoco.xml /app/reports/
                cp -r target/site/jacoco /app/reports/html 2>/dev/null || true
                echo 'Docker 测试完成，报告已复制'
            else
                echo 'Docker 测试失败，未生成报告'
            fi
        "; then
        
        print_success "Docker 测试完成"
        
        # 检查结果
        if [[ -f "$reports_dir/jacoco.xml" ]]; then
            print_success "Docker 生成了 JaCoCo 报告"
            
            # 解析覆盖率
            local line_covered=$(grep -o 'type="LINE"[^>]*covered="[0-9]*"' "$reports_dir/jacoco.xml" | grep -o 'covered="[0-9]*"' | cut -d'"' -f2 | head -1)
            local line_missed=$(grep -o 'type="LINE"[^>]*missed="[0-9]*"' "$reports_dir/jacoco.xml" | grep -o 'missed="[0-9]*"' | cut -d'"' -f2 | head -1)
            
            if [[ -n "$line_covered" && -n "$line_missed" ]]; then
                local total=$((line_covered + line_missed))
                if [[ $total -gt 0 ]]; then
                    local percentage=$(echo "scale=2; $line_covered * 100 / $total" | bc 2>/dev/null || echo "计算失败")
                    print_success "Docker 覆盖率: $percentage% ($line_covered/$total 行)"
                fi
            fi
        else
            print_error "Docker 未生成 JaCoCo 报告"
        fi
    else
        print_error "Docker 测试失败"
    fi
    
    # 清理
    rm -rf "$reports_dir"
}

# 主函数
main() {
    print_info "开始简化测试验证..."
    
    # 创建并测试简单项目
    local project_dir=$(create_simple_project)
    
    if test_simple_project "$project_dir"; then
        print_success "本地 Maven 测试成功"
        
        # 测试 Docker 环境
        test_with_docker "$project_dir"
    else
        print_error "本地 Maven 测试失败"
        print_info "这表明基本的 JaCoCo 环境有问题"
    fi
    
    # 清理
    read -p "是否删除测试项目？(Y/n): " -r
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        rm -rf "$project_dir"
        print_info "测试项目已删除"
    else
        print_info "测试项目保留在: $project_dir"
    fi
}

# 运行主函数
main "$@"
