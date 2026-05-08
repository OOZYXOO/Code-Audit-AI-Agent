"""
安全漏洞扫描器
检测代码中的安全问题
"""

import ast
import re
from pathlib import Path
from typing import List

from .base import BaseScanner, Issue, Severity

class SecurityScanner(BaseScanner):
    """
    安全漏洞扫描器
    检测各种安全相关的代码问题
    """
    
    # 危险函数模式
    DANGEROUS_FUNCTIONS = {
        "eval": "unsafe_eval",
        "exec": "unsafe_eval",
        "os.system": "unsafe_system",
        "os.popen": "unsafe_system",
        "subprocess.call": "unsafe_subprocess",
        "subprocess.run": "unsafe_subprocess",
        "subprocess.Popen": "unsafe_subprocess",
    }
    
    # 硬编码密钥的正则模式
    SECRET_PATTERNS = [
        # API Key 模式
        (r'api[_-]?key\s*=\s*[\'\"][A-Za-z0-9]{32,}[\'\"]', "api_key"),
        # Secret Key 模式
        (r'secret[_-]?key\s*=\s*[\'\"][A-Za-z0-9]{32,}[\'\"]', "secret_key"),
        # Password 模式
        (r'password\s*=\s*[\'\"][^\'\"]{8,}[\'\"]', "password"),
        # Access Token 模式
        (r'access[_-]?token\s*=\s*[\'\"][A-Za-z0-9]{32,}[\'\"]', "access_token"),
        # AWS Key 模式
        (r'AKIA[0-9A-Z]{16}', "aws_key"),
    ]
    
    def scan_file(self, file_path: Path, content: str, tree: ast.AST) -> List[Issue]:
        """
        扫描文件中的安全问题
        """
        self.issues = []
        
        # 遍历AST节点
        self._visit_node(tree, file_path, content)
        
        # 检查硬编码密钥
        self._check_hardcoded_secrets(file_path, content)
        
        return self.issues
    
    def _visit_node(self, node: ast.AST, file_path: Path, content: str):
        """递归访问AST节点"""
        # 检查裸except
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                self._add_issue(
                    file_path=file_path,
                    line=node.lineno,
                    issue_type="bare_except",
                    title="裸except语句",
                    description="使用了裸except语句，这会捕获所有异常，包括系统退出信号，可能隐藏关键错误。建议指定具体的异常类型。",
                    severity=Severity.WARNING,
                    node=node,
                    content=content
                )
        
        # 检查不安全的函数调用
        elif isinstance(node, ast.Call):
            self._check_dangerous_call(node, file_path, content)
        
        # 检查SQL注入风险
        elif isinstance(node, ast.BinOp):
            self._check_sql_concatenation(node, file_path, content)
        
        # 检查不安全的随机数
        elif isinstance(node, ast.Name):
            if node.id == "random":
                # 检测是否使用了random模块进行安全相关的操作
                pass
        
        # 递归访问子节点
        for child in ast.iter_child_nodes(node):
            self._visit_node(child, file_path, content)
    
    def _check_dangerous_call(self, node: ast.Call, file_path: Path, content: str):
        """检查危险函数调用"""
        # 获取函数名
        func_name = self._get_full_func_name(node.func)
        
        if func_name in self.DANGEROUS_FUNCTIONS:
            issue_type = self.DANGEROUS_FUNCTIONS[func_name]
            
            # 检查参数是否是字面量，如果是字面量可能风险较低
            has_risk = not all(isinstance(arg, ast.Constant) for arg in node.args)
            
            if issue_type == "unsafe_eval":
                self._add_issue(
                    file_path=file_path,
                    line=node.lineno,
                    issue_type=issue_type,
                    title="不安全的eval/exec调用",
                    description=f"使用了不安全的{func_name}函数，如果传入的参数包含用户可控内容，可能导致代码注入攻击。",
                    severity=Severity.CRITICAL if has_risk else Severity.WARNING,
                    node=node,
                    content=content
                )
            elif issue_type in ["unsafe_system", "unsafe_subprocess"]:
                self._add_issue(
                    file_path=file_path,
                    line=node.lineno,
                    issue_type=issue_type,
                    title="不安全的系统命令调用",
                    description=f"使用了{func_name}执行系统命令，如果参数包含用户可控内容，可能导致命令注入攻击。",
                    severity=Severity.CRITICAL if has_risk else Severity.WARNING,
                    node=node,
                    content=content
                )
    
    def _check_sql_concatenation(self, node: ast.BinOp, file_path: Path, content: str):
        """检查SQL字符串拼接，检测SQL注入风险"""
        # 检查是否是字符串拼接
        if not isinstance(node.op, ast.Add):
            return
        
        # 检查是否看起来像SQL查询
        left_str = self._get_constant_string(node.left)
        right_str = self._get_constant_string(node.right)
        
        # 如果有任何一边不是常量，说明可能是变量拼接
        if (left_str is not None and right_str is None) or \
           (left_str is None and right_str is not None):
            
            # 检查是否包含SQL关键词
            sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "WHERE"]
            full_str = (left_str or "") + (right_str or "")
            
            if any(keyword in full_str.upper() for keyword in sql_keywords):
                self._add_issue(
                    file_path=file_path,
                    line=node.lineno,
                    issue_type="sql_injection",
                    title="潜在的SQL注入风险",
                    description="检测到SQL查询字符串拼接，这可能导致SQL注入漏洞。建议使用参数化查询。",
                    severity=Severity.ERROR,
                    node=node,
                    content=content
                )
    
    def _check_hardcoded_secrets(self, file_path: Path, content: str):
        """检查硬编码的密钥"""
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            line_num = i + 1
            for pattern, secret_type in self.SECRET_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    self._add_issue(
                        file_path=file_path,
                        line=line_num,
                        issue_type="hardcoded_secret",
                        title=f"硬编码的{secret_type}",
                        description=f"检测到硬编码的{secret_type}，这会导致密钥泄露风险。建议使用环境变量或配置文件。",
                        severity=Severity.CRITICAL,
                        content=content
                    )
    
    def _get_full_func_name(self, node: ast.AST) -> str:
        """获取完整的函数名，包括模块名"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # 递归获取属性链
            prefix = self._get_full_func_name(node.value)
            return f"{prefix}.{node.attr}" if prefix else node.attr
        return ""
    
    def _get_constant_string(self, node: ast.AST) -> Optional[str]:
        """获取常量字符串，如果不是常量返回None"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.FormattedValue):
            # f-string中的变量，不是常量
            return None
        return None
    
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
