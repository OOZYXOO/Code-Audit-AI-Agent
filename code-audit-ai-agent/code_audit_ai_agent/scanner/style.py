"""
代码规范扫描器
检测代码规范问题
"""

import ast
import re
from pathlib import Path
from typing import List, Set

from .base import BaseScanner, Issue, Severity

class StyleScanner(BaseScanner):
    """
    代码规范扫描器
    检测PEP8规范、文档字符串等问题
    """
    
    # 行长度限制
    MAX_LINE_LENGTH = 88
    
    # 变量名模式
    VAR_NAME_PATTERN = re.compile(r'^[a-z_][a-z0-9_]*$')
    CLASS_NAME_PATTERN = re.compile(r'^[A-Z][a-zA-Z0-9]*$')
    
    def __init__(self):
        super().__init__()
    
    def scan_file(self, file_path: Path, content: str, tree: ast.AST) -> List[Issue]:
        """
        扫描文件中的规范问题
        """
        self.issues = []
        
        # 检查行长度
        self._check_line_length(file_path, content)
        
        # 遍历AST节点
        self._visit_node(tree, file_path, content)
        
        return self.issues
    
    def _check_line_length(self, file_path: Path, content: str):
        """检查行长度是否超过限制"""
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            line_num = i + 1
            # 忽略空行和注释行
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            if len(line) > self.MAX_LINE_LENGTH:
                self._add_issue(
                    file_path=file_path,
                    line=line_num,
                    issue_type="line_too_long",
                    title="行长度超过限制",
                    description=f"行长度为{len(line)}，超过了PEP8建议的{self.MAX_LINE_LENGTH}字符限制。",
                    severity=Severity.INFO,
                    content=content
                )
    
    def _visit_node(self, node: ast.AST, file_path: Path, content: str):
        """递归访问AST节点"""
        # 检查函数定义
        if isinstance(node, ast.FunctionDef):
            self._check_function(node, file_path, content)
        
        # 检查类定义
        elif isinstance(node, ast.ClassDef):
            self._check_class(node, file_path, content)
        
        # 检查变量名
        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):  # 只检查赋值
                self._check_variable_name(node, file_path, content)
        
        # 检查未使用的导入
        elif isinstance(node, ast.Import):
            for name in node.names:
                # 简单检测：记录导入的名字，后面检查是否被使用
                pass
        elif isinstance(node, ast.ImportFrom):
            for name in node.names:
                pass
        
        # 检查未使用的变量
        # 这需要更复杂的分析，这里做简单的启发式
        
        # 递归访问子节点
        for child in ast.iter_child_nodes(node):
            self._visit_node(child, file_path, content)
    
    def _check_function(self, node: ast.FunctionDef, file_path: Path, content: str):
        """检查函数定义"""
        # 检查文档字符串
        if not node.body or not isinstance(node.body[0], ast.Expr) or \
           not isinstance(node.body[0].value, ast.Constant) or \
           not isinstance(node.body[0].value.value, str):
            
            # 忽略简单的测试函数和私有函数？
            if not node.name.startswith("_") and len(node.body) > 1:
                self._add_issue(
                    file_path=file_path,
                    line=node.lineno,
                    issue_type="missing_docstring",
                    title="缺失文档字符串",
                    description=f"函数 `{node.name}` 缺少文档字符串。添加文档字符串可以提高代码的可维护性。",
                    severity=Severity.INFO,
                    node=node,
                    content=content
                )
        
        # 检查函数复杂度
        # 简单检测：如果函数行数太多
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
        func_lines = end_line - node.lineno + 1
        if func_lines > 50:
            self._add_issue(
                file_path=file_path,
                line=node.lineno,
                issue_type="too_complex",
                title="函数过于复杂",
                description=f"函数 `{node.name}` 有{func_lines}行，过于复杂。建议拆分成更小的函数。",
                severity=Severity.WARNING,
                node=node,
                content=content
            )
        
        # 检查函数名
        if not self.VAR_NAME_PATTERN.match(node.name):
            self._add_issue(
                file_path=file_path,
                line=node.lineno,
                issue_type="naming_convention",
                title="函数名不符合PEP8",
                description=f"函数名 `{node.name}` 不符合snake_case命名规范。",
                severity=Severity.INFO,
                node=node,
                content=content
            )
    
    def _check_class(self, node: ast.ClassDef, file_path: Path, content: str):
        """检查类定义"""
        # 检查文档字符串
        if not node.body or not isinstance(node.body[0], ast.Expr) or \
           not isinstance(node.body[0].value, ast.Constant) or \
           not isinstance(node.body[0].value.value, str):
            self._add_issue(
                file_path=file_path,
                line=node.lineno,
                issue_type="missing_docstring",
                title="类缺失文档字符串",
                description=f"类 `{node.name}` 缺少文档字符串。",
                severity=Severity.INFO,
                node=node,
                content=content
            )
        
        # 检查类名
        if not self.CLASS_NAME_PATTERN.match(node.name):
            self._add_issue(
                file_path=file_path,
                line=node.lineno,
                issue_type="naming_convention",
                title="类名不符合PEP8",
                description=f"类名 `{node.name}` 不符合CamelCase命名规范。",
                severity=Severity.INFO,
                node=node,
                content=content
            )
    
    def _check_variable_name(self, node: ast.Name, file_path: Path, content: str):
        """检查变量名"""
        # 忽略特殊变量
        if node.name.startswith("_"):
            return
        
        # 忽略大写常量
        if node.name.isupper():
            return
        
        if not self.VAR_NAME_PATTERN.match(node.name):
            self._add_issue(
                file_path=file_path,
                line=node.lineno,
                issue_type="naming_convention",
                title="变量名不符合PEP8",
                description=f"变量名 `{node.name}` 不符合snake_case命名规范。",
                severity=Severity.INFO,
                node=node,
                content=content
            )
    
    def _add_issue(self, file_path: Path, line: int, issue_type: str, 
                  title: str, description: str, severity: Severity,
                  node=None, content: str = None):
        """添加问题"""
        # 获取代码片段
        code_snippet = None
        if content:
            lines = content.splitlines()
            if 0 <= line - 1 < len(lines):
                code_snippet = lines[line - 1].strip()
        
        issue = Issue(
            issue_type=issue_type,
            severity=severity,
            title=title,
            description=description,
            file_path=file_path,
            line_number=line,
            node=node,
            code_snippet=code_snippet,
        )
        self.add_issue(issue)
