"""
日志工具
"""

import logging
import sys
from typing import Optional

# 全局日志器
_loggers = {}

def setup_logger(verbose: bool = False):
    """
    设置日志配置
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # 配置根日志器
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    
    return get_logger("code_audit_ai_agent")

def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        _loggers[name] = logger
    return _loggers[name]
