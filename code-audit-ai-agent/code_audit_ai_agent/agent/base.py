"""
AI Agent 基础模块
定义了Agent的基础接口和数据结构
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
import json

from ..scanner.base import Issue

@dataclass
class FixSuggestion:
    """
    修复建议
    """
    # 关联的问题
    issue: Issue
    
    # 修复后的代码
    fixed_code: str
    
    # 原始代码
    original_code: str
    
    # 修复说明
    explanation: str
    
    # 行范围
    start_line: int
    end_line: int
    
    # 是否可以自动应用
    can_auto_apply: bool = True
    
    # 置信度
    confidence: float = 0.9
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "issue": self.issue.to_dict(),
            "fixed_code": self.fixed_code,
            "original_code": self.original_code,
            "explanation": self.explanation,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "can_auto_apply": self.can_auto_apply,
            "confidence": self.confidence,
        }
    
    def to_diff(self) -> str:
        """生成diff格式"""
        lines = []
        lines.append(f"--- {self.issue.file_path}")
        lines.append(f"+++ {self.issue.file_path}")
        lines.append(f"@@ -{self.start_line},{self.end_line - self.start_line + 1} +{self.start_line},{self.end_line - self.start_line + 1} @@")
        
        for line in self.original_code.splitlines():
            lines.append(f"-{line}")
        for line in self.fixed_code.splitlines():
            lines.append(f"+{line}")
        
        return "\n".join(lines)

class AIAgent:
    """
    AI Agent 基类
    所有具体的LLM实现都应该继承这个类
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get("llm_provider", "openai")
    
    async def analyze_issues(self, issues: List[Issue], file_content: str) -> Dict[str, Any]:
        """
        分析问题，生成根因分析
        
        Args:
            issues: 发现的问题列表
            file_content: 文件内容
            
        Returns:
            分析结果
        """
        raise NotImplementedError
    
    async def generate_fix(self, issue: Issue, file_content: str) -> Optional[FixSuggestion]:
        """
        为单个问题生成修复建议
        
        Args:
            issue: 要修复的问题
            file_content: 文件完整内容
            
        Returns:
            修复建议
        """
        raise NotImplementedError
    
    async def batch_generate_fixes(self, issues: List[Issue], file_content: str) -> List[FixSuggestion]:
        """
        批量生成修复建议
        
        Args:
            issues: 问题列表
            file_content: 文件内容
            
        Returns:
            修复建议列表
        """
        fixes = []
        for issue in issues:
            fix = await self.generate_fix(issue, file_content)
            if fix:
                fixes.append(fix)
        return fixes
    
    def build_prompt(self, issue: Issue, file_content: str) -> str:
        """
        构建发送给LLM的prompt
        
        Args:
            issue: 问题
            file_content: 文件内容
            
        Returns:
            完整的prompt
        """
        # 获取问题附近的代码上下文
        lines = file_content.splitlines()
        issue_line = issue.line_number - 1  # 0-based
        
        # 取前后10行作为上下文
        context_start = max(0, issue_line - 10)
        context_end = min(len(lines), issue_line + 11)
        
        context_lines = lines[context_start:context_end]
        context_with_line_numbers = []
        
        for i, line in enumerate(context_lines):
            actual_line = context_start + i + 1
            marker = ">> " if actual_line == issue.line_number else "   "
            context_with_line_numbers.append(f"{actual_line:4d} {marker}{line}")
        
        context_code = "\n".join(context_with_line_numbers)
        
        prompt = f"""你是一个专业的Python代码审计专家，需要分析并修复代码中的问题。

文件: {issue.file_path}
问题位置: 第 {issue.line_number} 行
问题类型: {issue.issue_type}
严重级别: {issue.severity.value}
问题标题: {issue.title}
问题描述: {issue.description}

相关代码上下文:
```python
{context_code}
```

请分析这个问题，并生成修复方案。修复后的代码必须：
1. 完全解决当前的问题
2. 保持代码的原有功能不变
3. 符合PEP8代码规范
4. 尽可能简洁，只修改必要的部分
5. 不要删除任何注释或日志

请以JSON格式返回结果，包含以下字段：
- fixed_code: 修复后的代码片段（只包含需要修改的那几行）
- original_code: 原始的代码片段
- explanation: 修复说明，解释你做了什么修改，为什么这么改
- start_line: 修改的起始行号
- end_line: 修改的结束行号
- can_auto_apply: 是否可以自动应用这个修复
- confidence: 你对这个修复的置信度(0-1)

注意：只返回JSON，不要有其他内容。
"""
        return prompt
    
    def parse_response(self, response: str, issue: Issue) -> Optional[FixSuggestion]:
        """
        解析LLM的响应
        
        Args:
            response: LLM的响应文本
            issue: 关联的问题
            
        Returns:
            解析后的FixSuggestion
        """
        try:
            # 尝试提取JSON
            # 有时候LLM会用markdown包裹，需要处理
            json_str = response.strip()
            
            # 移除markdown代码块
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            json_str = json_str.strip()
            data = json.loads(json_str)
            
            # 验证必要字段
            required_fields = ["fixed_code", "original_code", "explanation", "start_line", "end_line"]
            for field in required_fields:
                if field not in data:
                    return None
            
            suggestion = FixSuggestion(
                issue=issue,
                fixed_code=data["fixed_code"],
                original_code=data["original_code"],
                explanation=data["explanation"],
                start_line=data["start_line"],
                end_line=data["end_line"],
                can_auto_apply=data.get("can_auto_apply", True),
                confidence=data.get("confidence", 0.9),
            )
            
            return suggestion
            
        except Exception as e:
            # 解析失败
            return None
