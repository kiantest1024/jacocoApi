"""工具函数模块"""

import os
import subprocess
import tempfile
import shutil
from datetime import datetime


def run_command(command, cwd=None, timeout=300):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"
    except Exception as e:
        return -1, "", str(e)


def create_temp_dir(prefix="jacoco_"):
    """创建临时目录"""
    return tempfile.mkdtemp(prefix=prefix)


def cleanup_temp_dir(temp_dir):
    """清理临时目录"""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def ensure_dir(directory):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_timestamp():
    """获取时间戳"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def parse_git_url(url):
    """解析Git URL获取项目信息"""
    if url.endswith('.git'):
        url = url[:-4]
    
    parts = url.split('/')
    if len(parts) >= 2:
        return parts[-1], parts[-2]  # project_name, namespace
    
    return parts[-1] if parts else "unknown", "unknown"


def is_docker_available():
    """检查Docker是否可用"""
    try:
        result = subprocess.run(['docker', 'info'], 
                              capture_output=True, 
                              timeout=10)
        return result.returncode == 0
    except:
        return False


def is_maven_available():
    """检查Maven是否可用"""
    try:
        result = subprocess.run(['mvn', '--version'], 
                              capture_output=True, 
                              timeout=10)
        return result.returncode == 0
    except:
        return False


def extract_coverage_from_xml(xml_file):
    """从JaCoCo XML文件提取覆盖率数据"""
    if not os.path.exists(xml_file):
        return None
    
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        coverage_data = {}
        
        # 查找总体覆盖率计数器
        for counter in root.findall('.//counter'):
            counter_type = counter.get('type')
            missed = int(counter.get('missed', 0))
            covered = int(counter.get('covered', 0))
            total = missed + covered
            
            if total > 0:
                percentage = (covered / total) * 100
                coverage_data[counter_type.lower()] = {
                    'covered': covered,
                    'missed': missed,
                    'total': total,
                    'percentage': round(percentage, 2)
                }
        
        return coverage_data
    except Exception as e:
        print(f"解析覆盖率XML失败: {e}")
        return None


def format_coverage_message(coverage_data, service_name):
    """格式化覆盖率消息"""
    if not coverage_data:
        return f"📊 {service_name} 覆盖率扫描完成，但未获取到覆盖率数据"
    
    line_data = coverage_data.get('line', {})
    branch_data = coverage_data.get('branch', {})
    instruction_data = coverage_data.get('instruction', {})
    
    message = f"📊 {service_name} 覆盖率报告\n\n"
    
    if line_data:
        message += f"📈 行覆盖率: {line_data['percentage']}% ({line_data['covered']}/{line_data['total']})\n"
    
    if branch_data:
        message += f"🌿 分支覆盖率: {branch_data['percentage']}% ({branch_data['covered']}/{branch_data['total']})\n"
    
    if instruction_data:
        message += f"⚡ 指令覆盖率: {instruction_data['percentage']}% ({instruction_data['covered']}/{instruction_data['total']})\n"
    
    message += f"\n⏰ 扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return message


def log_info(message, request_id=""):
    """记录信息日志"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    prefix = f"[{request_id}]" if request_id else ""
    print(f"[{timestamp}] {prefix} INFO: {message}")


def log_error(message, request_id=""):
    """记录错误日志"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    prefix = f"[{request_id}]" if request_id else ""
    print(f"[{timestamp}] {prefix} ERROR: {message}")


def log_warning(message, request_id=""):
    """记录警告日志"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    prefix = f"[{request_id}]" if request_id else ""
    print(f"[{timestamp}] {prefix} WARNING: {message}")


def log_success(message, request_id=""):
    """记录成功日志"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    prefix = f"[{request_id}]" if request_id else ""
    print(f"[{timestamp}] {prefix} SUCCESS: {message}")
