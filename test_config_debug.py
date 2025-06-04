#!/usr/bin/env python3
"""
调试配置加载问题
验证配置是否正确传递
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_loading():
    """测试配置加载"""
    print("🔧 测试配置加载")
    print("=" * 50)
    
    try:
        # 测试config.py中的配置
        print("1. 测试config.py中的配置...")
        from config import DEFAULT_SCAN_CONFIG, get_service_config
        
        print("DEFAULT_SCAN_CONFIG:")
        for key, value in DEFAULT_SCAN_CONFIG.items():
            print(f"  {key}: {value}")
        
        # 测试获取服务配置
        test_url = "http://172.16.1.30/kian/jacocotest.git"
        config = get_service_config(test_url)
        
        print(f"\nget_service_config('{test_url}'):")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        # 检查关键配置
        print(f"\n关键配置检查:")
        print(f"  force_local_scan: {config.get('force_local_scan', 'NOT_SET')}")
        print(f"  use_docker: {config.get('use_docker', 'NOT_SET')}")
        print(f"  use_shared_container: {config.get('use_shared_container', 'NOT_SET')}")
        
        return config
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_app_config():
    """测试app.py中的配置函数"""
    print("\n🔧 测试app.py中的配置函数")
    print("=" * 50)
    
    try:
        # 测试app.py中的get_service_config
        print("2. 测试app.py中的get_service_config...")
        
        # 模拟导入app模块
        import importlib.util
        spec = importlib.util.spec_from_file_location("app", "app.py")
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        
        test_url = "http://172.16.1.30/kian/jacocotest.git"
        app_config = app_module.get_service_config(test_url)
        
        print(f"app.get_service_config('{test_url}'):")
        for key, value in app_config.items():
            print(f"  {key}: {value}")
        
        # 检查关键配置
        print(f"\n关键配置检查:")
        print(f"  force_local_scan: {app_config.get('force_local_scan', 'NOT_SET')}")
        print(f"  use_docker: {app_config.get('use_docker', 'NOT_SET')}")
        print(f"  use_shared_container: {app_config.get('use_shared_container', 'NOT_SET')}")
        
        return app_config
        
    except Exception as e:
        print(f"❌ app配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_jacoco_tasks_config():
    """测试jacoco_tasks中的配置处理"""
    print("\n🔧 测试jacoco_tasks中的配置处理")
    print("=" * 50)
    
    try:
        from jacoco_tasks import run_jacoco_scan_docker
        from config import get_service_config
        
        # 获取配置
        test_url = "http://172.16.1.30/kian/jacocotest.git"
        service_config = get_service_config(test_url)
        
        print("传递给jacoco_tasks的配置:")
        for key, value in service_config.items():
            print(f"  {key}: {value}")
        
        # 模拟配置检查逻辑
        print(f"\n配置逻辑检查:")
        force_local = service_config.get('force_local_scan', False)
        use_docker = service_config.get('use_docker', True)
        use_shared = service_config.get('use_shared_container', True)
        
        print(f"  force_local_scan: {force_local} (类型: {type(force_local)})")
        print(f"  use_docker: {use_docker} (类型: {type(use_docker)})")
        print(f"  use_shared_container: {use_shared} (类型: {type(use_shared)})")
        
        # 模拟决策逻辑
        if force_local:
            print("  决策: 应该使用本地扫描 ✅")
        elif use_docker and not force_local:
            print("  决策: 应该使用Docker扫描 ❌")
        else:
            print("  决策: 应该使用本地扫描 ✅")
        
        return service_config
        
    except Exception as e:
        print(f"❌ jacoco_tasks配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_configs(config1, config2, name1, name2):
    """比较两个配置"""
    print(f"\n🔍 比较配置: {name1} vs {name2}")
    print("=" * 50)
    
    if not config1 or not config2:
        print("❌ 无法比较，其中一个配置为空")
        return
    
    # 找出所有键
    all_keys = set(config1.keys()) | set(config2.keys())
    
    differences = []
    for key in sorted(all_keys):
        val1 = config1.get(key, "NOT_SET")
        val2 = config2.get(key, "NOT_SET")
        
        if val1 != val2:
            differences.append((key, val1, val2))
            print(f"  {key}:")
            print(f"    {name1}: {val1}")
            print(f"    {name2}: {val2}")
        else:
            print(f"  {key}: {val1} ✅")
    
    if differences:
        print(f"\n❌ 发现 {len(differences)} 个配置差异")
        return False
    else:
        print(f"\n✅ 配置完全一致")
        return True

def main():
    """主函数"""
    print("🧪 配置调试测试")
    print("=" * 50)
    
    # 1. 测试config.py配置
    config_py_result = test_config_loading()
    
    # 2. 测试app.py配置
    app_py_result = test_app_config()
    
    # 3. 测试jacoco_tasks配置
    jacoco_tasks_result = test_jacoco_tasks_config()
    
    # 4. 比较配置
    if config_py_result and app_py_result:
        configs_match = compare_configs(
            config_py_result, app_py_result, 
            "config.py", "app.py"
        )
        
        if not configs_match:
            print("\n❌ 发现配置不一致问题！")
            print("💡 这解释了为什么强制本地扫描没有生效")
        else:
            print("\n✅ 配置一致")
    
    # 5. 总结
    print("\n" + "=" * 50)
    print("📊 调试结果总结:")
    
    if config_py_result:
        force_local = config_py_result.get('force_local_scan', False)
        print(f"  config.py force_local_scan: {force_local}")
    
    if app_py_result:
        force_local = app_py_result.get('force_local_scan', False)
        print(f"  app.py force_local_scan: {force_local}")
    
    if jacoco_tasks_result:
        force_local = jacoco_tasks_result.get('force_local_scan', False)
        print(f"  jacoco_tasks force_local_scan: {force_local}")
    
    # 检查配置文件内容
    print(f"\n📄 检查config.py文件内容:")
    try:
        with open('config.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'force_local_scan": True' in content:
            print("  ✅ config.py中确实设置了force_local_scan: True")
        elif 'force_local_scan": False' in content:
            print("  ❌ config.py中设置了force_local_scan: False")
        else:
            print("  ⚠️ config.py中未找到force_local_scan设置")
            
        if 'use_docker": False' in content:
            print("  ✅ config.py中确实设置了use_docker: False")
        elif 'use_docker": True' in content:
            print("  ❌ config.py中设置了use_docker: True")
        else:
            print("  ⚠️ config.py中未找到use_docker设置")
            
    except Exception as e:
        print(f"  ❌ 读取config.py失败: {e}")

if __name__ == "__main__":
    main()
