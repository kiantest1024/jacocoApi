"""
扫描器模块，包含不同的代码覆盖率扫描实现。
"""

from .base import BaseScannerStrategy
from .jacoco import JaCoCoScannerStrategy
from .solution2 import Solution2ScannerStrategy

__all__ = [
    'BaseScannerStrategy',
    'JaCoCoScannerStrategy',
    'Solution2ScannerStrategy',
    'get_scanner_strategy'
]

def get_scanner_strategy(scan_method: str) -> BaseScannerStrategy:
    """
    根据扫描方法名称获取相应的扫描器策略。
    
    参数:
        scan_method: 扫描方法名称
        
    返回:
        扫描器策略实例
    """
    if scan_method == "solution1" or scan_method == "jacoco":
        return JaCoCoScannerStrategy()
    elif scan_method == "solution2":
        return Solution2ScannerStrategy()
    else:
        raise ValueError(f"未知的扫描方法: {scan_method}")
