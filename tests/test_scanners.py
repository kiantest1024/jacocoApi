"""
扫描器模块的单元测试。
"""

import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

import pytest

from scanners import get_scanner_strategy, BaseScannerStrategy, JaCoCoScannerStrategy, Solution2ScannerStrategy


def test_get_scanner_strategy():
    """测试获取扫描器策略。"""
    # 测试 solution1/jacoco 扫描方法
    scanner = get_scanner_strategy("solution1")
    assert isinstance(scanner, JaCoCoScannerStrategy)
    
    scanner = get_scanner_strategy("jacoco")
    assert isinstance(scanner, JaCoCoScannerStrategy)
    
    # 测试 solution2 扫描方法
    scanner = get_scanner_strategy("solution2")
    assert isinstance(scanner, Solution2ScannerStrategy)
    
    # 测试未知扫描方法
    with pytest.raises(ValueError):
        get_scanner_strategy("unknown")


def test_base_scanner_strategy():
    """测试扫描器策略基类。"""
    # 基类的抽象方法应该引发 NotImplementedError
    scanner = BaseScannerStrategy()
    
    with pytest.raises(NotImplementedError):
        scanner.scan("repo_url", "commit_id", "branch_name", {})
    
    with pytest.raises(NotImplementedError):
        scanner.parse_results("results_path")


@patch('subprocess.run')
def test_clone_repository(mock_run):
    """测试克隆仓库方法。"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 设置模拟返回值
        mock_run.return_value = MagicMock()
        
        # 创建扫描器实例
        scanner = BaseScannerStrategy()
        
        # 测试克隆仓库
        result = scanner.clone_repository("git@example.com:user/repo.git", temp_dir)
        assert result is True
        
        # 验证调用
        mock_run.assert_called()
        args, kwargs = mock_run.call_args_list[0]
        assert args[0][0] == "git"
        assert args[0][1] == "clone"
        
        # 测试克隆仓库并检出特定提交
        mock_run.reset_mock()
        result = scanner.clone_repository("git@example.com:user/repo.git", temp_dir, "abcdef")
        assert result is True
        
        # 验证调用
        assert mock_run.call_count == 2
        args, kwargs = mock_run.call_args_list[1]
        assert args[0][0] == "git"
        assert args[0][1] == "checkout"
        assert args[0][2] == "abcdef"
        
        # 测试克隆失败
        mock_run.reset_mock()
        mock_run.side_effect = Exception("Clone failed")
        result = scanner.clone_repository("git@example.com:user/repo.git", temp_dir)
        assert result is False
    
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


@patch.object(JaCoCoScannerStrategy, 'clone_repository')
@patch('subprocess.run')
def test_jacoco_scanner_scan(mock_run, mock_clone):
    """测试 JaCoCo 扫描器的扫描方法。"""
    # 设置模拟返回值
    mock_clone.return_value = True
    mock_run.return_value = MagicMock()
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建模拟的 JaCoCo XML 报告
        report_dir = os.path.join(temp_dir, "results")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "jacoco.xml")
        
        # 写入模拟的 XML 内容
        with open(report_path, 'w') as f:
            f.write("""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <report name="Example">
                <counter type="INSTRUCTION" missed="1000" covered="4000"/>
                <counter type="BRANCH" missed="500" covered="1500"/>
                <counter type="LINE" missed="200" covered="800"/>
                <counter type="COMPLEXITY" missed="100" covered="400"/>
                <counter type="METHOD" missed="50" covered="150"/>
                <counter type="CLASS" missed="10" covered="40"/>
            </report>
            """)
        
        # 模拟 tempfile.mkdtemp 返回我们的临时目录
        with patch('tempfile.mkdtemp', return_value=temp_dir):
            # 创建扫描器实例
            scanner = JaCoCoScannerStrategy()
            
            # 测试扫描
            service_config = {
                "jacoco_jar_path": "/path/to/jacococli.jar",
                "source_dirs": ["src/main/java"],
                "class_dirs": ["target/classes"],
                "run_maven_build": True
            }
            
            result = scanner.scan(
                "git@example.com:user/repo.git",
                "abcdef",
                "main",
                service_config
            )
            
            # 验证结果
            assert result["status"] == "success"
            assert result["coverage_percentage"] == 80.0  # 800 / (800 + 200) * 100
            assert result["lines_covered"] == 800
            assert result["lines_total"] == 1000
            assert "detailed_coverage" in result
            assert result["detailed_coverage"]["line_coverage"] == 80.0
            assert result["detailed_coverage"]["instruction_coverage"] == 80.0  # 4000 / (4000 + 1000) * 100
            
            # 验证调用
            mock_clone.assert_called_once()
            assert mock_run.call_count >= 2  # Maven build + JaCoCo


@patch.object(Solution2ScannerStrategy, 'clone_repository')
@patch('subprocess.run')
def test_solution2_scanner_scan(mock_run, mock_clone):
    """测试 Solution2 扫描器的扫描方法。"""
    # 设置模拟返回值
    mock_clone.return_value = True
    mock_run.return_value = MagicMock()
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建模拟的 coverage.py JSON 报告
        report_dir = os.path.join(temp_dir, "results")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "coverage.json")
        
        # 写入模拟的 JSON 内容
        with open(report_path, 'w') as f:
            f.write("""
            {
                "totals": {
                    "covered_lines": 800,
                    "num_statements": 1000,
                    "covered_branches": 150,
                    "num_branches": 200,
                    "missing_lines": 200
                }
            }
            """)
        
        # 模拟 tempfile.mkdtemp 返回我们的临时目录
        with patch('tempfile.mkdtemp', return_value=temp_dir):
            # 创建扫描器实例
            scanner = Solution2ScannerStrategy()
            
            # 测试扫描
            service_config = {
                "coverage_settings_path": "/path/to/coverage-settings.xml",
                "custom_command": "python -m pytest --cov=."
            }
            
            result = scanner.scan(
                "git@example.com:user/repo.git",
                "abcdef",
                "main",
                service_config
            )
            
            # 验证结果
            assert result["status"] == "success"
            assert result["coverage_percentage"] == 80.0  # 800 / 1000 * 100
            assert result["lines_covered"] == 800
            assert result["lines_total"] == 1000
            assert "detailed_coverage" in result
            assert result["detailed_coverage"]["line_coverage"] == 80.0
            assert result["detailed_coverage"]["branch_coverage"] == 75.0  # 150 / 200 * 100
            assert result["settings_used"] == "/path/to/coverage-settings.xml"
            
            # 验证调用
            mock_clone.assert_called_once()
            assert mock_run.call_count >= 3  # pip install + coverage run + coverage json
