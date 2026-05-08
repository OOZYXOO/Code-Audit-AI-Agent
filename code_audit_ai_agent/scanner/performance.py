"""
性能瓶颈扫描器
检测代码中的性能问题
"""

import ast
from pathlib import Path
from typing import List, Set, Dict

from .base import BaseScanner, Issue, Severity

class PerformanceScanner(BaseScanner):
    """
    性能瓶颈扫描器
    检测各种性能相关的代码问题
    """
    
    def __init__(self):
        super().__init__()
        # 用于跟踪循环内的变量
        self.loop_depth = 0
        # 跟踪变量赋值
        self.loop_assignments: Dict[int, Set[str]] = {}
    
    def scan_file(self, file_path: Path, content: str, tree: ast.AST) -> List[Issue]:
        """
        扫描文件中的性能问题
        """
        self.issues = []
        self.loop_depth = 0
        self.loop_assignments = {}
        
        # 遍历AST节点
        self._visit_node(tree, file_path, content)
        
        return self.issues
    
    def _visit_node(self, node: ast.AST, file_path: Path, content: str):
        """递归访问AST节点"""
        # 检查循环
        is_loop = False
        if isinstance(node, (ast.For, ast.While)):
            self.loop_depth += 1
            self.loop_assignments[self.loop_depth] = set()
            is_loop = True
            
            # 检查嵌套循环
            if self.loop_depth >= 2:
                # 检测嵌套循环
                self._check_nested_loop(node, file_path, content)
        
        # 检查循环内的字符串拼接
        if self.loop_depth > 0 and isinstance(node, ast.AugAssign):
            if isinstance(node.op, ast.Add):
                # 检测 s += "string" 这种模式
                if isinstance(node.target, ast.Name):
                    var_name = node.target.id
                    # 检查是否是字符串拼接
                    if self._is_string_concat_candidate(node.value):
                        self._add_issue(
                            file_path=file_path,
                            line=node.lineno,
                            issue_type="string_concat_loop",
                            title="循环内字符串拼接",
                            description="在循环中使用 += 进行字符串拼接，这在Python中效率很低，因为字符串是不可变的。建议使用列表收集然后用 ''.join()。",
                            severity=Severity.WARNING,
                            node=node,
                            content=content
                        )
        
        # 检查大列表的重复遍历
        if isinstance(node, ast.Call):
            self._check_repeated_iteration(node, file_path, content)
        
        # 检查不必要的大对象拷贝
        if isinstance(node, ast.Assign):
            self._check_large_object_copy(node, file_path, content)
        
        # 递归访问子节点
        for child in ast.iter_child_nodes(node):
            self._visit_node(child, file_path, content)
        
        # 循环结束，恢复深度
        if is_loop:
            del self.loop_assignments[self.loop_depth]
            self.loop_depth -= 1
    
    def _check_nested_loop(self, node: ast.For, file_path: Path, content: str):
        """检查嵌套循环"""
        # 检查内层循环是否遍历了不同的列表
        # 简单检测：如果两个循环都有iter，且不是range，可能是O(n^2)
        if isinstance(node.iter, ast.Name):
            iter_name = node.iter.id
            # 检查内层循环的体中是否有对外部列表的访问
            # 这是一个简单的启发式检测
            self._add_issue(
                file_path=file_path,
                line=node.lineno,
                issue_type="nested_loop",
                title="嵌套循环",
                description="检测到嵌套循环，这可能导致O(n²)的时间复杂度。如果处理大数据集，这会成为性能瓶颈。",
                severity=Severity.WARNING,
                node=node,
                content=content
            )
    
    def _check_repeated_iteration(self, node: ast.Call, file_path: Path, content: str):
        """检查重复遍历大列表"""
        # 检测 len(large_list) 在循环内的调用
        if isinstance(node.func, ast.Name) and node.func.id == "len":
            if node.args and isinstance(node.args[0], ast.Name):
                arg_name = node.args[0].id
                # 如果在循环内调用 len(list)，这本身没问题
                # 但如果多次调用，可能有优化空间
                pass
        
        # 检测 sorted() 或其他可能的O(n log n)操作
        if isinstance(node.func, ast.Name) and node.func.id in ["sorted", "list", "tuple"]:
            if node.args and self.loop_depth > 0:
                # 在循环内转换列表，可能有问题
                self._add_issue(
                    file_path=file_path,
                    line=node.lineno,
                    issue_type="repeated_iteration",
                    title="循环内重复列表转换",
                    description="在循环内重复对列表进行转换操作，这会导致重复遍历。建议在循环外完成。",
                    severity=Severity.INFO,
                    node=node,
                    content=content
                )
    
    def _check_large_object_copy(self, node: ast.Assign, file_path: Path, content: str):
        """检查不必要的大对象拷贝"""
        # 检测 deepcopy 的使用
        for target in node.targets:
            if isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Attribute):
                    if node.value.func.attr == "deepcopy":
                        self._add_issue(
                            file_path=file_path,
                            line=node.lineno,
                            issue_type="large_object_copy",
                            title="深度拷贝操作",
                            description="使用了deepcopy，这可能会对大对象造成性能开销。确认是否真的需要完整的深度拷贝。",
                            severity=Severity.INFO,
                            node=node,
                            content=content
                        )
    
    def _is_string_concat_candidate(self, node: ast.AST) -> bool:
        """检查是否是字符串拼接的候选"""
        # 简单检查：如果是字符串常量，很可能是字符串拼接
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        # 如果是f-string
        if isinstance(node, ast.JoinedStr):
            return True
        # 如果是其他变量，也可能是字符串
        if isinstance(node, ast.Name):
            return True
        return False
    
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
