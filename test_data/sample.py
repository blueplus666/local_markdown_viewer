#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例Python文件
用于集成测试的示例代码
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional


class SampleClass:
    """示例类"""
    
    def __init__(self, name: str, value: int = 0):
        """
        初始化示例类
        
        Args:
            name: 名称
            value: 数值
        """
        self.name = name
        self.value = value
        self._private_attr = "private"
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取信息
        
        Returns:
            包含信息的字典
        """
        return {
            "name": self.name,
            "value": self.value,
            "type": self.__class__.__name__
        }
    
    def increment(self, amount: int = 1) -> int:
        """
        增加数值
        
        Args:
            amount: 增加的数量
            
        Returns:
            增加后的数值
        """
        self.value += amount
        return self.value
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"SampleClass(name='{self.name}', value={self.value})"


def sample_function(param1: str, param2: Optional[int] = None) -> bool:
    """
    示例函数
    
    Args:
        param1: 第一个参数
        param2: 第二个参数（可选）
        
    Returns:
        操作是否成功
    """
    print(f"参数1: {param1}")
    if param2 is not None:
        print(f"参数2: {param2}")
    
    return True


def process_data(data: list) -> list:
    """
    处理数据
    
    Args:
        data: 输入数据列表
        
    Returns:
        处理后的数据列表
    """
    result = []
    
    for item in data:
        if isinstance(item, (int, float)):
            result.append(item * 2)
        elif isinstance(item, str):
            result.append(item.upper())
        else:
            result.append(item)
    
    return result


def main() -> int:
    """
    主函数
    
    Returns:
        退出码
    """
    print("=== 示例程序开始 ===")
    
    # 创建示例对象
    obj = SampleClass("测试对象", 10)
    print(f"创建对象: {obj}")
    
    # 调用方法
    info = obj.get_info()
    print(f"对象信息: {info}")
    
    # 增加数值
    new_value = obj.increment(5)
    print(f"增加后的数值: {new_value}")
    
    # 调用示例函数
    success = sample_function("测试参数", 42)
    print(f"函数调用结果: {success}")
    
    # 处理数据
    test_data = [1, 2, "hello", 3.14, "world"]
    processed_data = process_data(test_data)
    print(f"原始数据: {test_data}")
    print(f"处理后数据: {processed_data}")
    
    print("=== 示例程序结束 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# 测试代码
def test_sample_class():
    """测试SampleClass"""
    obj = SampleClass("测试", 5)
    assert obj.name == "测试"
    assert obj.value == 5
    assert obj.increment(3) == 8


def test_sample_function():
    """测试sample_function"""
    assert sample_function("test") == True
    assert sample_function("test", 123) == True


def test_process_data():
    """测试process_data"""
    data = [1, 2, "hello"]
    result = process_data(data)
    assert result == [2, 4, "HELLO"]


if __name__ == "__main__":
    # 运行测试
    test_sample_class()
    test_sample_function()
    test_process_data()
    print("所有测试通过！") 