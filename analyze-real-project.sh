#!/bin/bash

# 分析真实项目 jacocotest 的覆盖率问题
set -e

echo "🔍 分析真实项目 jacocotest 的覆盖率问题"
echo "======================================="

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

REPO_URL="http://172.16.1.30/kian/jacocotest.git"
CURRENT_DIR=$(pwd)
PROJECT_DIR="$CURRENT_DIR/real_project_analysis"

# 清理旧分析
cleanup_old() {
    if [[ -d "$PROJECT_DIR" ]]; then
        rm -rf "$PROJECT_DIR"
    fi
}

# 克隆项目
clone_project() {
    print_info "克隆真实项目..."
    
    cleanup_old
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    print_success "项目克隆成功"
}

# 分析项目结构
analyze_structure() {
    print_info "分析项目结构..."
    
    echo "📁 项目根目录文件:"
    ls -la
    
    echo ""
    echo "📁 源代码结构:"
    if [[ -d "src" ]]; then
        find src -type f -name "*.java" | head -20
        
        echo ""
        echo "📊 代码统计:"
        local main_files=$(find src/main/java -name "*.java" 2>/dev/null | wc -l)
        local test_files=$(find src/test/java -name "*.java" 2>/dev/null | wc -l)
        print_info "主代码文件: $main_files 个"
        print_info "测试文件: $test_files 个"
    else
        print_warning "src 目录不存在"
    fi
}

# 分析测试文件内容
analyze_test_content() {
    print_info "分析测试文件内容..."
    
    local test_files=$(find src/test/java -name "*.java" 2>/dev/null)
    
    for test_file in $test_files; do
        echo "📄 分析测试文件: $test_file"
        
        echo "  导入语句:"
        grep "^import" "$test_file" | head -5
        
        echo "  测试方法:"
        grep -n "@Test\|@ParameterizedTest" "$test_file" | head -5
        
        echo "  主代码调用:"
        grep -n "new \|Main\|Database\|Login" "$test_file" | head -5 || echo "    未找到明显的主代码调用"
        
        echo "  断言语句:"
        grep -n "assert\|verify\|expect" "$test_file" | head -3 || echo "    未找到断言语句"
        
        echo "  ========================"
    done
}

# 分析主代码
analyze_main_code() {
    print_info "分析主代码..."
    
    local main_files=$(find src/main/java -name "*.java" 2>/dev/null)
    
    for main_file in $main_files; do
        echo "📄 主代码文件: $main_file"
        
        echo "  类定义:"
        grep -n "^public class\|^class" "$main_file" || echo "    未找到类定义"
        
        echo "  公共方法:"
        grep -n "public.*(" "$main_file" | head -5 || echo "    未找到公共方法"
        
        echo "  ========================"
    done
}

# 手动运行测试并分析
manual_test_analysis() {
    print_info "手动运行测试并分析..."
    
    # 清理
    mvn clean -q
    
    # 编译主代码
    print_info "编译主代码..."
    if mvn compile -q; then
        print_success "主代码编译成功"
        
        echo "编译后的主代码类:"
        find target/classes -name "*.class" 2>/dev/null | head -10
    else
        print_error "主代码编译失败"
        mvn compile
        return 1
    fi
    
    # 编译测试代码
    print_info "编译测试代码..."
    if mvn test-compile -q; then
        print_success "测试代码编译成功"
        
        echo "编译后的测试类:"
        find target/test-classes -name "*.class" 2>/dev/null | head -10
    else
        print_error "测试代码编译失败"
        mvn test-compile
        return 1
    fi
    
    # 运行单个测试方法
    print_info "尝试运行单个测试..."
    
    # 查找测试类
    local test_classes=$(find target/test-classes -name "*Test.class" | sed 's|target/test-classes/||' | sed 's|\.class||' | sed 's|/|.|g')
    
    for test_class in $test_classes; do
        print_info "运行测试类: $test_class"
        
        # 运行测试并显示详细输出
        mvn test -Dtest="$test_class" -Dmaven.test.failure.ignore=true
        
        # 检查测试输出
        if [[ -f "target/surefire-reports/TEST-${test_class}.xml" ]]; then
            echo "测试报告内容:"
            cat "target/surefire-reports/TEST-${test_class}.xml"
        fi
        
        break  # 只测试第一个测试类
    done
}

# 强制运行 JaCoCo 并详细分析
force_jacoco_analysis() {
    print_info "强制运行 JaCoCo 并详细分析..."
    
    # 清理
    mvn clean -q
    
    # 显式运行 JaCoCo prepare-agent
    print_info "运行 JaCoCo prepare-agent..."
    mvn jacoco:prepare-agent -X > jacoco_prepare.log 2>&1
    
    echo "JaCoCo prepare-agent 关键日志:"
    grep -i "argline\|jacoco\|agent" jacoco_prepare.log | tail -10
    
    # 编译和运行测试
    mvn compile test-compile -q
    
    # 运行测试
    print_info "运行测试..."
    mvn surefire:test -Dmaven.test.failure.ignore=true -X > test_execution.log 2>&1
    
    echo "测试执行关键日志:"
    grep -i "running\|test\|jacoco" test_execution.log | tail -15
    
    # 检查 JaCoCo 执行数据
    if [[ -f "target/jacoco.exec" ]]; then
        local exec_size=$(stat -c%s "target/jacoco.exec" 2>/dev/null || echo "0")
        print_success "JaCoCo 执行数据文件存在，大小: $exec_size bytes"
        
        if [[ $exec_size -gt 0 ]]; then
            print_success "JaCoCo 收集到执行数据"
        else
            print_warning "JaCoCo 执行数据为空"
            
            # 分析为什么为空
            echo "可能的原因:"
            echo "1. 测试没有真正执行主代码"
            echo "2. JaCoCo 代理没有正确附加"
            echo "3. 类路径问题"
        fi
    else
        print_error "JaCoCo 执行数据文件不存在"
    fi
    
    # 生成报告
    print_info "生成 JaCoCo 报告..."
    mvn jacoco:report -X > jacoco_report.log 2>&1
    
    echo "JaCoCo 报告生成日志:"
    tail -20 jacoco_report.log
    
    # 分析报告
    if [[ -f "target/site/jacoco/jacoco.xml" ]]; then
        print_success "JaCoCo XML 报告已生成"
        
        echo "报告内容:"
        cat target/site/jacoco/jacoco.xml
        
        # 解析覆盖率
        local line_covered=$(grep -o 'type="LINE"[^>]*covered="[0-9]*"' "target/site/jacoco/jacoco.xml" | grep -o 'covered="[0-9]*"' | cut -d'"' -f2 | head -1)
        local line_missed=$(grep -o 'type="LINE"[^>]*missed="[0-9]*"' "target/site/jacoco/jacoco.xml" | grep -o 'missed="[0-9]*"' | cut -d'"' -f2 | head -1)
        
        if [[ -n "$line_covered" && -n "$line_missed" ]]; then
            local total=$((line_covered + line_missed))
            if [[ $total -gt 0 ]]; then
                local percentage=$(echo "scale=2; $line_covered * 100 / $total" | bc 2>/dev/null || echo "计算失败")
                print_info "覆盖率: $percentage% ($line_covered/$total 行)"
                
                if [[ $(echo "$percentage > 0" | bc 2>/dev/null) -eq 1 ]]; then
                    print_success "🎉 找到了覆盖率数据！"
                else
                    print_warning "覆盖率仍为 0%"
                fi
            else
                print_warning "总行数为 0"
            fi
        else
            print_warning "无法解析覆盖率数据"
        fi
    else
        print_error "JaCoCo XML 报告未生成"
    fi
}

# 比较与工作项目的差异
compare_with_working_project() {
    print_info "比较与工作项目的差异..."
    
    echo "🔍 关键差异分析:"
    
    # 检查 pom.xml 差异
    echo "1. pom.xml 配置:"
    if grep -q "jacoco-maven-plugin" pom.xml; then
        print_success "包含 JaCoCo 插件"
    else
        print_warning "缺少 JaCoCo 插件"
    fi
    
    if grep -q "maven-surefire-plugin" pom.xml; then
        print_success "包含 Surefire 插件"
        
        # 检查版本
        local surefire_version=$(grep -A 5 "maven-surefire-plugin" pom.xml | grep "<version>" | sed 's/.*<version>\(.*\)<\/version>.*/\1/')
        print_info "Surefire 版本: $surefire_version"
    else
        print_warning "缺少 Surefire 插件"
    fi
    
    # 检查依赖
    echo ""
    echo "2. 测试依赖:"
    if grep -q "junit-jupiter" pom.xml; then
        print_success "包含 JUnit 5"
    else
        print_warning "缺少 JUnit 5"
    fi
    
    if grep -q "mockito" pom.xml; then
        print_success "包含 Mockito"
    else
        print_warning "缺少 Mockito"
    fi
    
    if grep -q "assertj" pom.xml; then
        print_success "包含 AssertJ"
    else
        print_warning "缺少 AssertJ"
    fi
    
    # 检查测试代码质量
    echo ""
    echo "3. 测试代码质量:"
    local test_methods=$(grep -r "@Test" src/test/java/ | wc -l)
    print_info "测试方法数量: $test_methods"
    
    local main_calls=$(grep -r "new \|Main\|Database\|Login" src/test/java/ | wc -l)
    print_info "可能的主代码调用: $main_calls"
}

# 生成修复建议
generate_fix_suggestions() {
    print_info "生成修复建议..."
    
    cat > fix_suggestions.md << 'EOF'
# 真实项目 JaCoCo 覆盖率修复建议

## 问题分析

基于分析结果，可能的问题包括：

### 1. 测试代码问题
- 测试方法存在但不真正调用主代码
- 使用了过多的 Mock 对象，替代了真实代码执行
- 测试逻辑有问题，没有覆盖到主要代码路径

### 2. 配置问题
- JaCoCo 插件配置不正确
- Surefire 插件版本不兼容
- 缺少必要的测试依赖

### 3. 代码结构问题
- 主代码和测试代码包结构不匹配
- 类路径配置问题

## 修复步骤

### 步骤 1: 验证测试真正执行主代码
在主代码方法中添加 System.out.println 验证是否被调用：

```java
public int add(int a, int b) {
    System.out.println("add method called with: " + a + ", " + b);
    return a + b;
}
```

### 步骤 2: 简化测试代码
移除不必要的 Mock，直接调用真实代码：

```java
@Test
public void testAdd() {
    Calculator calc = new Calculator();  // 直接创建对象
    int result = calc.add(2, 3);         // 直接调用方法
    assertEquals(5, result);             // 验证结果
}
```

### 步骤 3: 更新 pom.xml 配置
确保包含正确的插件和依赖配置。

### 步骤 4: 逐步调试
1. 先确保测试能运行
2. 再确保 JaCoCo 能收集数据
3. 最后确保报告能正确生成
EOF

    print_success "修复建议已保存到 fix_suggestions.md"
}

# 主函数
main() {
    clone_project
    analyze_structure
    analyze_test_content
    analyze_main_code
    manual_test_analysis
    force_jacoco_analysis
    compare_with_working_project
    generate_fix_suggestions
    
    cd "$CURRENT_DIR"
    
    print_info "分析完成，结果保存在: $PROJECT_DIR"
    
    # 询问是否保留分析结果
    read -p "是否保留分析结果？(Y/n): " -r
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        cleanup_old
        print_info "分析结果已删除"
    else
        print_info "分析结果保留在: $PROJECT_DIR"
    fi
}

# 运行主函数
main "$@"
