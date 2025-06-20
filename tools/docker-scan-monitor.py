#!/usr/bin/env python3
"""
Docker 扫描监控工具
用于诊断和监控 Docker 扫描过程中的问题
"""

import subprocess
import time
import threading
import signal
import sys
import os

class DockerScanMonitor:
    def __init__(self):
        self.container_id = None
        self.monitoring = False
        self.start_time = None
        
    def find_jacoco_containers(self):
        """查找正在运行的 JaCoCo 容器"""
        try:
            result = subprocess.run([
                'docker', 'ps', '--filter', 'ancestor=jacoco-scanner:latest', 
                '--format', '{{.ID}} {{.Status}} {{.Command}}'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split(' ', 2)
                        if len(parts) >= 2:
                            containers.append({
                                'id': parts[0],
                                'status': parts[1],
                                'command': parts[2] if len(parts) > 2 else ''
                            })
                return containers
            return []
        except Exception as e:
            print(f"❌ 查找容器失败: {e}")
            return []
    
    def get_container_logs(self, container_id, lines=50):
        """获取容器日志"""
        try:
            result = subprocess.run([
                'docker', 'logs', '--tail', str(lines), container_id
            ], capture_output=True, text=True, timeout=10)
            
            return result.stdout + result.stderr
        except Exception as e:
            print(f"❌ 获取容器日志失败: {e}")
            return ""
    
    def get_container_stats(self, container_id):
        """获取容器资源使用情况"""
        try:
            result = subprocess.run([
                'docker', 'stats', '--no-stream', '--format', 
                'table {{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}',
                container_id
            ], capture_output=True, text=True, timeout=10)
            
            return result.stdout
        except Exception as e:
            print(f"❌ 获取容器统计失败: {e}")
            return ""
    
    def exec_in_container(self, container_id, command):
        """在容器中执行命令"""
        try:
            result = subprocess.run([
                'docker', 'exec', container_id, 'sh', '-c', command
            ], capture_output=True, text=True, timeout=30)
            
            return result.stdout + result.stderr
        except Exception as e:
            print(f"❌ 容器内执行命令失败: {e}")
            return ""
    
    def monitor_container(self, container_id):
        """监控容器状态"""
        print(f"🔍 开始监控容器: {container_id}")
        self.container_id = container_id
        self.monitoring = True
        self.start_time = time.time()
        
        while self.monitoring:
            try:
                # 检查容器是否还在运行
                result = subprocess.run([
                    'docker', 'ps', '-q', '--filter', f'id={container_id}'
                ], capture_output=True, text=True, timeout=5)
                
                if not result.stdout.strip():
                    print("📋 容器已停止")
                    break
                
                # 显示运行时间
                elapsed = time.time() - self.start_time
                print(f"⏱️  运行时间: {elapsed:.1f}秒")
                
                # 获取容器统计信息
                stats = self.get_container_stats(container_id)
                if stats:
                    lines = stats.strip().split('\n')
                    if len(lines) > 1:  # 跳过表头
                        print(f"📊 资源使用: {lines[1]}")
                
                # 检查容器内部进程
                processes = self.exec_in_container(container_id, "ps aux")
                if processes:
                    # 查找 Maven 或 Java 进程
                    maven_processes = [line for line in processes.split('\n') 
                                     if 'mvn' in line or 'java' in line]
                    if maven_processes:
                        print(f"🔨 活跃进程: {len(maven_processes)} 个 Maven/Java 进程")
                        for proc in maven_processes[:3]:  # 只显示前3个
                            print(f"   {proc.strip()}")
                
                # 检查最新日志
                recent_logs = self.get_container_logs(container_id, 5)
                if recent_logs:
                    print("📝 最新日志:")
                    for line in recent_logs.split('\n')[-3:]:
                        if line.strip():
                            print(f"   {line.strip()}")
                
                print("-" * 60)
                time.sleep(10)  # 每10秒检查一次
                
            except KeyboardInterrupt:
                print("\n⚠️  监控被中断")
                break
            except Exception as e:
                print(f"❌ 监控过程出错: {e}")
                time.sleep(5)
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
    
    def kill_container(self, container_id):
        """强制停止容器"""
        try:
            print(f"🛑 强制停止容器: {container_id}")
            subprocess.run(['docker', 'kill', container_id], timeout=10)
            print("✅ 容器已停止")
        except Exception as e:
            print(f"❌ 停止容器失败: {e}")

def test_docker_scan_directly():
    """直接测试 Docker 扫描"""
    print("🧪 直接测试 Docker 扫描...")
    
    # 使用较短的超时时间进行测试
    test_command = [
        'docker', 'run', '--rm', 
        '-v', '/tmp/test_jacoco:/workspace/reports',
        'jacoco-scanner:latest',
        '--repo-url', 'http://172.16.1.30/kian/jacocotest.git',
        '--commit-id', 'main',
        '--branch', 'main',
        '--service-name', 'jacocotest'
    ]
    
    print(f"📋 测试命令: {' '.join(test_command)}")
    
    try:
        # 创建测试目录
        os.makedirs('/tmp/test_jacoco', exist_ok=True)
        
        # 启动进程但不等待完成
        process = subprocess.Popen(
            test_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"🚀 测试进程已启动，PID: {process.pid}")
        print("💡 让进程运行30秒，然后检查状态...")
        
        # 等待30秒
        try:
            stdout, stderr = process.communicate(timeout=30)
            print("✅ 测试在30秒内完成")
            print(f"📤 输出: {stdout}")
            if stderr:
                print(f"📥 错误: {stderr}")
        except subprocess.TimeoutExpired:
            print("⏰ 测试超过30秒，进程可能卡住了")
            print("🛑 终止测试进程...")
            process.kill()
            stdout, stderr = process.communicate()
            print(f"📤 部分输出: {stdout}")
            if stderr:
                print(f"📥 部分错误: {stderr}")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def main():
    """主函数"""
    print("🔍 Docker 扫描监控工具")
    print("=" * 40)
    
    # 设置信号处理
    monitor = DockerScanMonitor()
    
    def signal_handler(sig, frame):
        print("\n🛑 收到中断信号，停止监控...")
        monitor.stop_monitoring()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    while True:
        print("\n📋 选择操作:")
        print("1. 查找正在运行的 JaCoCo 容器")
        print("2. 监控指定容器")
        print("3. 直接测试 Docker 扫描")
        print("4. 强制停止所有 JaCoCo 容器")
        print("5. 退出")
        
        choice = input("\n请选择 (1-5): ").strip()
        
        if choice == "1":
            print("\n🔍 查找 JaCoCo 容器...")
            containers = monitor.find_jacoco_containers()
            
            if containers:
                print(f"📋 找到 {len(containers)} 个容器:")
                for i, container in enumerate(containers, 1):
                    print(f"{i}. ID: {container['id']}")
                    print(f"   状态: {container['status']}")
                    print(f"   命令: {container['command']}")
                    print()
            else:
                print("📋 未找到正在运行的 JaCoCo 容器")
        
        elif choice == "2":
            containers = monitor.find_jacoco_containers()
            
            if not containers:
                print("❌ 未找到正在运行的容器")
                continue
            
            if len(containers) == 1:
                container_id = containers[0]['id']
            else:
                print("📋 选择要监控的容器:")
                for i, container in enumerate(containers, 1):
                    print(f"{i}. {container['id']} - {container['status']}")
                
                try:
                    idx = int(input("请选择容器编号: ")) - 1
                    container_id = containers[idx]['id']
                except (ValueError, IndexError):
                    print("❌ 无效选择")
                    continue
            
            print(f"\n🔍 开始监控容器: {container_id}")
            print("💡 按 Ctrl+C 停止监控")
            
            try:
                monitor.monitor_container(container_id)
            except KeyboardInterrupt:
                print("\n⚠️  监控已停止")
        
        elif choice == "3":
            test_docker_scan_directly()
        
        elif choice == "4":
            containers = monitor.find_jacoco_containers()
            
            if containers:
                print(f"🛑 强制停止 {len(containers)} 个容器...")
                for container in containers:
                    monitor.kill_container(container['id'])
            else:
                print("📋 未找到需要停止的容器")
        
        elif choice == "5":
            print("👋 退出监控工具")
            break
        
        else:
            print("❌ 无效选择")

if __name__ == "__main__":
    main()
