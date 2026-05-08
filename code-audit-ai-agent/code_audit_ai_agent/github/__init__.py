"""
GitHub集成模块
负责与GitHub API交互，自动创建PR和触发CI
"""

from .client import GitHubManager

__all__ = ["GitHubManager"]
