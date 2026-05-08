"""
AI Agent模块
负责与大语言模型交互，生成修复建议
"""

from typing import Dict, Any
from .base import AIAgent, FixSuggestion
from .openai_agent import OpenAIAgent
from .anthropic_agent import AnthropicAgent
from .mimo_agent import MiMoAgent

__all__ = [
    "AIAgent",
    "FixSuggestion",
    "OpenAIAgent",
    "AnthropicAgent",
    "MiMoAgent",
    "create_agent",
]

def create_agent(config: Dict[str, Any]) -> AIAgent:
    """
    根据配置创建对应的Agent实例
    
    Args:
        config: 配置字典
        
    Returns:
        AIAgent实例
    """
    provider = config.get("llm_provider", "openai").lower()
    
    if provider == "openai":
        return OpenAIAgent(config)
    elif provider == "anthropic":
        return AnthropicAgent(config)
    elif provider == "mimo":
        return MiMoAgent(config)
    else:
        raise ValueError(f"不支持的LLM提供商: {provider}")
