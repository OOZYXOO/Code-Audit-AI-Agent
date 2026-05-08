"""
OpenAI Agent 实现
使用OpenAI的API进行代码修复
"""

import json
from typing import List, Optional, Dict, Any
import openai
from openai import AsyncOpenAI

from .base import AIAgent, FixSuggestion
from ..scanner.base import Issue
from ..utils.logger import get_logger

logger = get_logger(__name__)

class OpenAIAgent(AIAgent):
    """
    使用OpenAI GPT模型的AI Agent
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("llm_api_key")
        self.model = config.get("llm_model", "gpt-4o")
        self.base_url = config.get("llm_base_url")
        
        # 初始化客户端
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
    
    async def analyze_issues(self, issues: List[Issue], file_content: str) -> Dict[str, Any]:
        """
        分析文件中的所有问题
        """
        issues_desc = []
        for issue in issues:
            issues_desc.append({
                "type": issue.issue_type,
                "severity": issue.severity.value,
                "title": issue.title,
                "line": issue.line_number,
                "code": issue.code_snippet,
            })
        
        prompt = f"""请分析这个Python文件中的所有问题，并给出总体评估。

文件内容:
```python
{file_content[:2000]}  # 限制长度
```

发现的问题:
{json.dumps(issues_desc, indent=2, ensure_ascii=False)}

请返回一个JSON，包含：
- fixable_count: 可以自动修复的问题数量
- manual_count: 需要人工处理的问题数量
- health_score: 总体健康评分(0-100)
- summary: 简短的总结
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500,
            )
            
            result_text = response.choices[0].message.content
            # 解析JSON
            result_text = result_text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:-3]
            
            return json.loads(result_text)
            
        except Exception as e:
            logger.error(f"OpenAI分析失败: {e}")
            return {
                "fixable_count": len(issues),
                "manual_count": 0,
                "health_score": 50,
                "summary": "分析失败",
            }
    
    async def generate_fix(self, issue: Issue, file_content: str) -> Optional[FixSuggestion]:
        """
        生成修复建议
        """
        prompt = self.build_prompt(issue, file_content)
        
        try:
            logger.debug(f"调用OpenAI修复问题: {issue.title}")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
            )
            
            response_text = response.choices[0].message.content
            if not response_text:
                return None
            
            # 解析响应
            fix = self.parse_response(response_text, issue)
            return fix
            
        except Exception as e:
            logger.error(f"生成修复失败: {e}")
            return None
