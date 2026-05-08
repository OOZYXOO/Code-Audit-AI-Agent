"""
Code Audit AI Agent - 自动化代码审计与优化的AI Agent

一个强大的自动化代码审计工具，能够自动扫描代码仓库中的安全漏洞、性能瓶颈和代码规范问题，
利用大语言模型的长链推理能力自动生成修复方案，并通过GitHub API自动提交优化PR。
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .scanner.base import Issue, Severity, CodeScanner
from .agent.base import AIAgent, FixSuggestion
from .github.client import GitHubManager
from .auditor import CodeAuditor

__all__ = [
    "Issue",
    "Severity", 
    "CodeScanner",
    "AIAgent",
    "FixSuggestion",
    "GitHubManager",
    "CodeAuditor",
]
