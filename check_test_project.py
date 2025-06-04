#!/usr/bin/env python3
"""
检查测试项目是否有测试用例
"""

import requests
import json

def check_project_structure():
    """检查GitLab项目结构"""
    
    # GitLab API URL (如果可访问)
    project_url = "http://172.16.1.30/kian/jacocotest"
    api_url = "http://172.16.1.30/api/v4/projects/kian%2Fjacocotest"
    
    print("🔍 检查测试项目结构")
    print("=" * 50)
    
    print(f"📋 项目URL: {project_url}")
    print(f"📋 API URL: {api_url}")
    
    # 尝试访问项目
    try:
        response = requests.get(project_url, timeout=10)
        if response.status_code == 200:
            print("✅ 项目可访问")
        else:
            print(f"⚠️ 项目访问状态: {response.status_code}")
    except Exception as e:
        print(f"❌ 项目访问失败: {e}")
    
    # 检查常见的测试文件路径
    test_paths = [
        "src/test/java",
        "src/test/resources", 
        "test",
        "tests"
    ]
    
    print(f"\n🧪 常见测试目录:")
    for path in test_paths:
        print(f"  📁 {path}")
    
    print(f"\n💡 建议检查:")
    print("1. 项目是否有测试用例 (src/test/java/**/*Test.java)")
    print("2. 测试用例是否能正常运行")
    print("3. pom.xml是否配置了测试插件")
    
    # 提供手动检查命令
    print(f"\n🔧 手动检查命令:")
    print("git clone http://172.16.1.30/kian/jacocotest.git")
    print("cd jacocotest")
    print("find . -name '*Test.java' -o -name '*Tests.java'")
    print("mvn test")
    print("mvn jacoco:prepare-agent test jacoco:report")

def create_sample_test_commands():
    """创建示例测试命令"""
    
    commands = [
        "# 克隆项目",
        "git clone http://172.16.1.30/kian/jacocotest.git",
        "cd jacocotest",
        "",
        "# 检查项目结构", 
        "ls -la",
        "find . -name '*.java' | head -10",
        "find . -name '*Test.java'",
        "",
        "# 检查pom.xml",
        "cat pom.xml",
        "",
        "# 尝试编译",
        "mvn clean compile",
        "",
        "# 尝试运行测试",
        "mvn test",
        "",
        "# 尝试生成JaCoCo报告",
        "mvn jacoco:prepare-agent test jacoco:report",
        "",
        "# 查找生成的报告",
        "find target -name '*.xml' -o -name '*.html' | grep -i jacoco",
        "",
        "# 如果没有测试，创建一个简单的测试",
        "mkdir -p src/test/java/com/example",
        "cat > src/test/java/com/example/SimpleTest.java << 'EOF'",
        "package com.example;",
        "import org.junit.Test;",
        "import static org.junit.Assert.*;",
        "",
        "public class SimpleTest {",
        "    @Test",
        "    public void testSimple() {",
        "        assertTrue(\"This should pass\", true);",
        "        assertEquals(\"2 + 2 should equal 4\", 4, 2 + 2);",
        "    }",
        "}",
        "EOF"
    ]
    
    print("\n📝 手动测试脚本:")
    print("-" * 30)
    for cmd in commands:
        print(cmd)

if __name__ == "__main__":
    check_project_structure()
    create_sample_test_commands()
