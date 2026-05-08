"""
配置管理
"""

import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

def load_config() -> Dict[str, Any]:
    """
    加载配置
    从环境变量和.env文件加载
    """
    # 加载.env文件
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    
    # 也可以从用户主目录加载
    user_env = Path.home() / ".code-audit-ai-agent.env"
    if user_env.exists():
        load_dotenv(user_env)
    
    config = {
        # LLM配置
        "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
        "llm_api_key": os.getenv("LLM_API_KEY"),
        "llm_model": os.getenv("LLM_MODEL"),
        "llm_base_url": os.getenv("LLM_BASE_URL"),
        
        # GitHub配置
        "github_token": os.getenv("GITHUB_TOKEN"),
        
        # 其他配置
        "max_workers": int(os.getenv("MAX_WORKERS", "8")),
        "timeout": int(os.getenv("TIMEOUT", "60")),
    }
    
    # 设置默认模型
    if not config["llm_model"]:
        defaults = {
            "openai": "gpt-4o",
            "anthropic": "claude-3-7-sonnet-20240229",
            "mimo": "mimo-v2.5-pro",
        }
        config["llm_model"] = defaults.get(config["llm_provider"], "gpt-4o")
    
    return config

def validate_config(config: Dict[str, Any]) -> bool:
    """
    验证配置是否完整
    """
    if not config["llm_api_key"]:
        return False
    return True
