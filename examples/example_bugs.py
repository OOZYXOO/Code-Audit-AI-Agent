"""
示例代码，包含各种问题，用于测试代码审计工具
"""

import os
import subprocess
import random

# 这是一个硬编码的密钥，会被检测到
API_KEY = "sk_1234567890abcdefghijklmnopqrstuvwxyz"

def unsafe_function(user_input):
    """
    这个函数有安全问题
    """
    # 不安全的eval调用
    eval(user_input)  # 危险！
    
    # 不安全的系统调用
    os.system(f"echo {user_input}")  # 命令注入风险
    
    # SQL拼接，注入风险
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    execute_query(query)

def execute_query(query):
    # 执行查询
    pass

def process_items(items):
    """
    处理项目列表，有性能问题
    """
    result = ""
    # 循环内字符串拼接，性能差
    for item in items:
        result += str(item) + ", "  # 每次都创建新字符串
    
    return result

def nested_loop_example(data):
    """
    嵌套循环，O(n²)复杂度
    """
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if i != j:
                result.append(data[i] + data[j])
    return result

def bad_exception_handling():
    """
    不好的异常处理
    """
    try:
        # 一些操作
        x = 1 / 0
    except:  # 裸except，危险！
        print("出错了")

def missing_docstring_function(a, b):
    # 这个函数没有文档字符串
    return a + b

def too_long_function():
    # 这个函数太长了，会被检测到
    result = []
    for i in range(100):
        for j in range(100):
            for k in range(100):
                result.append(i * j * k)
    return result

# 过长的行，会被检测到
some_really_long_variable_name_that_violates_naming_convention = "this is a very long string that will cause the line to be way too long and violate the PEP8 line length limit of 88 characters"

if __name__ == "__main__":
    # 测试代码
    data = [1, 2, 3, 4, 5]
    process_items(data)
    nested_loop_example(data)
