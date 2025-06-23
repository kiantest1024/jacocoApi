#!/usr/bin/env python3
"""分析测试输出，提取关键信息"""

import re

def analyze_test_log(log_file):
    """分析测试日志文件"""
    
    print("🔍 分析测试日志...")
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")
        return
    
    lines = content.split('\n')
    
    # 提取关键信息
    test_results = {
        'compilation_errors': [],
        'test_failures': [],
        'test_successes': [],
        'build_status': 'unknown',
        'coverage_info': [],
        'maven_phases': []
    }
    
    current_phase = None
    in_test_output = False
    
    for line in lines:
        line = line.strip()
        
        # 检测 Maven 阶段
        if '[INFO] --- ' in line and '---' in line:
            phase_match = re.search(r'\[INFO\] --- (.*?) ---', line)
            if phase_match:
                current_phase = phase_match.group(1)
                test_results['maven_phases'].append(current_phase)
                print(f"📋 Maven 阶段: {current_phase}")
        
        # 检测编译错误
        if '[ERROR]' in line and ('COMPILATION ERROR' in line or 'cannot find symbol' in line or 'class' in line and 'should be declared' in line):
            test_results['compilation_errors'].append(line)
            print(f"🔴 编译错误: {line}")
        
        # 检测测试运行
        if 'Running ' in line and 'Test' in line:
            test_class = line.split('Running ')[-1].strip()
            print(f"🏃 运行测试: {test_class}")
            in_test_output = True
        
        # 检测测试结果
        if 'Tests run:' in line:
            test_results['test_successes'].append(line)
            print(f"📊 测试结果: {line}")
            in_test_output = False
        
        # 检测测试失败
        if in_test_output and ('FAILED' in line or 'ERROR' in line):
            test_results['test_failures'].append(line)
            print(f"❌ 测试失败: {line}")
        
        # 检测构建状态
        if '[INFO] BUILD SUCCESS' in line:
            test_results['build_status'] = 'success'
            print("✅ 构建成功")
        elif '[INFO] BUILD FAILURE' in line:
            test_results['build_status'] = 'failure'
            print("❌ 构建失败")
        
        # 检测 JaCoCo 相关信息
        if 'jacoco' in line.lower() or 'coverage' in line.lower():
            test_results['coverage_info'].append(line)
            print(f"📈 覆盖率信息: {line}")
    
    # 总结分析结果
    print("\n" + "="*60)
    print("📊 测试日志分析结果")
    print("="*60)
    
    print(f"🔨 Maven 阶段数: {len(test_results['maven_phases'])}")
    if test_results['maven_phases']:
        print(f"   最后阶段: {test_results['maven_phases'][-1]}")
    
    print(f"🔴 编译错误数: {len(test_results['compilation_errors'])}")
    if test_results['compilation_errors']:
        print("   编译错误详情:")
        for error in test_results['compilation_errors'][:5]:  # 只显示前5个
            print(f"     {error}")
    
    print(f"✅ 测试成功数: {len(test_results['test_successes'])}")
    print(f"❌ 测试失败数: {len(test_results['test_failures'])}")
    
    print(f"🏗️  构建状态: {test_results['build_status']}")
    
    print(f"📈 覆盖率信息数: {len(test_results['coverage_info'])}")
    
    # 提供建议
    print("\n" + "="*60)
    print("💡 建议")
    print("="*60)
    
    if test_results['compilation_errors']:
        print("🔧 发现编译错误，建议:")
        print("   1. 检查测试文件的类名和文件名是否匹配")
        print("   2. 确认所有必要的导入语句")
        print("   3. 运行: python tools/quick-fix-jacocotest.py")
    
    elif test_results['build_status'] == 'success':
        print("🎉 构建成功！")
        if not test_results['test_successes']:
            print("⚠️  但没有运行测试，可能测试代码有问题")
        else:
            print("✅ 测试正常运行")
    
    elif test_results['build_status'] == 'failure':
        print("❌ 构建失败，需要修复错误")
    
    else:
        print("⚠️  构建状态未知，可能日志不完整")

def extract_key_lines(log_file, output_file):
    """提取关键行到新文件"""
    
    print(f"📄 提取关键信息到: {output_file}")
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")
        return
    
    lines = content.split('\n')
    key_lines = []
    
    keywords = [
        '[ERROR]', '[WARN]', 'COMPILATION ERROR', 'BUILD FAILURE', 'BUILD SUCCESS',
        'Tests run:', 'Running ', 'FAILED', 'jacoco', 'coverage',
        'cannot find symbol', 'class', 'should be declared'
    ]
    
    for line in lines:
        if any(keyword in line for keyword in keywords):
            key_lines.append(line)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(key_lines))
        print(f"✅ 已提取 {len(key_lines)} 行关键信息")
    except Exception as e:
        print(f"❌ 写入文件失败: {e}")

def main():
    """主函数"""

    log_file = "errorDebug.txt"
    key_file = "key_errors.txt"
    
    print("🔍 JaCoCo 测试日志分析工具")
    print("="*40)
    
    # 分析完整日志
    analyze_test_log(log_file)
    
    # 提取关键信息
    extract_key_lines(log_file, key_file)
    
    print(f"\n📄 关键信息已保存到: {key_file}")
    print("💡 可以查看该文件获取简化的错误信息")

if __name__ == "__main__":
    main()
