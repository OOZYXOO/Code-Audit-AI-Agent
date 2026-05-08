#!/usr/bin/env python3
"""
Code Audit AI Agent 使用示例
"""

import asyncio
from pathlib import Path
from code_audit_ai_agent import CodeAuditor
from code_audit_ai_agent.utils.config import load_config

async def main():
    """
    演示如何使用Code Audit AI Agent
    """
    # 加载配置
    config = load_config()
    
    # 初始化审计器
    auditor = CodeAuditor(
        config=config,
        severity="warning",
    )
    
    # 要审计的目录，这里审计examples目录
    target_path = Path(__file__).parent
    
    print("=" * 60)
    print("Code Audit AI Agent 演示")
    print("=" * 60)
    
    # 1. 仅扫描
    print("\n📋 步骤1: 执行代码扫描...")
    issues = await auditor.scan_only(target_path)
    
    print(f"\n发现 {len(issues)} 个问题:")
    for issue in issues[:5]:  # 显示前5个
        print(f"  [{issue.severity.value}] {issue.file_path.name}:{issue.line_number} - {issue.title}")
    
    if len(issues) > 5:
        print(f"  ... 还有 {len(issues) - 5} 个问题")
    
    # 2. 分析
    if auditor.agent:
        print("\n🤖 步骤2: AI分析问题...")
        issues, analysis = await auditor.audit(target_path)
        
        print(f"\nAI分析结果:")
        print(f"  可自动修复: {analysis.get('fixable_count', 0)} 个问题")
        print(f"  需要人工: {analysis.get('manual_count', 0)} 个问题")
        print(f"  健康评分: {analysis.get('health_score', 0):.1f}/100")
        
        # 3. 试运行修复
        print("\n🔧 步骤3: 生成修复建议（试运行）...")
        issues, fixes = await auditor.fix(target_path, dry_run=True)
        
        print(f"\n生成了 {len(fixes)} 个修复建议:")
        for fix in fixes[:3]:
            print(f"  • {fix.issue.title}")
            print(f"    说明: {fix.explanation}")
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("\n要实际运行完整功能，请配置:")
    print("1. LLM_API_KEY - 大模型API密钥")
    print("2. GITHUB_TOKEN - GitHub令牌（可选，用于自动PR）")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
