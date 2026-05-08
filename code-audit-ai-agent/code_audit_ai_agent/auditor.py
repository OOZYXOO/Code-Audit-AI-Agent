"""
主审计器类
协调扫描、AI分析、修复和PR创建的完整工作流
"""

from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import asyncio

from .scanner import CodeScanner, Issue, Severity
from .agent import create_agent, FixSuggestion
from .github import GitHubManager
from .utils.logger import get_logger
from .utils.config import validate_config

logger = get_logger(__name__)

class CodeAuditor:
    """
    主代码审计器
    提供完整的代码审计工作流
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        severity: str = "warning",
        exclude_patterns: Optional[List[str]] = None,
        max_file_size_kb: int = 1000,
        parallel: int = 8,
    ):
        """
        初始化审计器
        
        Args:
            config: 配置字典
            severity: 最低严重级别
            exclude_patterns: 排除的模式
            max_file_size_kb: 最大文件大小
            parallel: 并行数
        """
        self.config = config
        
        # 转换严重级别
        severity_map = {
            "info": Severity.INFO,
            "warning": Severity.WARNING,
            "error": Severity.ERROR,
            "critical": Severity.CRITICAL,
        }
        severity_threshold = severity_map.get(severity, Severity.WARNING)
        
        # 初始化扫描器
        self.scanner = CodeScanner(
            severity_threshold=severity_threshold,
            exclude_patterns=exclude_patterns,
            max_file_size_kb=max_file_size_kb,
        )
        
        # 初始化AI Agent
        if validate_config(config):
            self.agent = create_agent(config)
        else:
            logger.warning("配置不完整，AI功能将不可用")
            self.agent = None
        
        # 初始化GitHub管理器
        self.github = None
        if config.get("github_token"):
            try:
                self.github = GitHubManager(config["github_token"])
            except Exception as e:
                logger.warning(f"GitHub初始化失败: {e}")
    
    async def scan_only(self, path: Path) -> List[Issue]:
        """
        仅执行扫描，不做分析
        """
        logger.info(f"开始扫描目录: {path}")
        issues = await self.scanner.scan_directory(path)
        
        # 统计
        by_type = {}
        for issue in issues:
            by_type[issue.issue_type] = by_type.get(issue.issue_type, 0) + 1
        
        logger.info(f"扫描完成，发现 {len(issues)} 个问题")
        return issues
    
    async def audit(self, path: Path) -> Tuple[List[Issue], Dict[str, Any]]:
        """
        扫描并分析
        """
        issues = await self.scan_only(path)
        
        if not self.agent:
            return issues, {}
        
        # 按文件分组进行分析
        by_file = {}
        for issue in issues:
            by_file.setdefault(issue.file_path, []).append(issue)
        
        total_analysis = {
            "fixable_count": 0,
            "manual_count": 0,
            "health_score": 100,
        }
        
        # 对每个文件进行分析
        for file_path, file_issues in by_file.items():
            try:
                # 读取文件内容
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # AI分析
                analysis = await self.agent.analyze_issues(file_issues, content)
                
                total_analysis["fixable_count"] += analysis.get("fixable_count", 0)
                total_analysis["manual_count"] += analysis.get("manual_count", 0)
                # 平均健康评分
                total_analysis["health_score"] = (
                    total_analysis["health_score"] + analysis.get("health_score", 50)
                ) / 2
                
            except Exception as e:
                logger.error(f"分析文件 {file_path} 失败: {e}")
        
        return issues, total_analysis
    
    async def fix(
        self,
        path: Path,
        dry_run: bool = False,
        interactive: bool = False,
    ) -> Tuple[List[Issue], List[FixSuggestion]]:
        """
        扫描并自动修复
        """
        issues, analysis = await self.audit(path)
        
        if not self.agent:
            logger.error("AI Agent未初始化，无法生成修复")
            return issues, []
        
        # 按文件分组
        by_file = {}
        for issue in issues:
            by_file.setdefault(issue.file_path, []).append(issue)
        
        all_fixes = []
        
        # 处理每个文件
        for file_path, file_issues in by_file.items():
            try:
                # 读取文件内容
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 为每个问题生成修复
                fixes = await self.agent.batch_generate_fixes(file_issues, content)
                
                if fixes:
                    all_fixes.extend(fixes)
                    
                    # 如果不是试运行，应用修复
                    if not dry_run:
                        await self._apply_fixes(file_path, fixes, content, interactive)
                
            except Exception as e:
                logger.error(f"处理文件 {file_path} 失败: {e}")
        
        return issues, all_fixes
    
    async def _apply_fixes(
        self,
        file_path: Path,
        fixes: List[FixSuggestion],
        content: str,
        interactive: bool,
    ):
        """
        应用修复到文件
        """
        # 按行号排序，从后往前应用，避免行号偏移
        fixes_sorted = sorted(fixes, key=lambda f: f.end_line, reverse=True)
        
        lines = content.splitlines(True)  # 保留换行符
        
        for fix in fixes_sorted:
            if not fix.can_auto_apply:
                logger.warning(f"跳过无法自动应用的修复: {fix.issue.title}")
                continue
            
            if interactive:
                # 交互式确认
                print(f"\n发现问题: {fix.issue.title}")
                print(f"位置: {file_path}:{fix.start_line}")
                print(f"原始代码: {fix.original_code}")
                print(f"修复代码: {fix.fixed_code}")
                print(f"说明: {fix.explanation}")
                
                response = input("是否应用此修复? [y/N] ").lower().strip()
                if response != "y":
                    logger.info("跳过此修复")
                    continue
            
            # 应用修复
            start_idx = fix.start_line - 1
            end_idx = fix.end_line
            
            # 替换行
            lines[start_idx:end_idx] = [line + "\n" for line in fix.fixed_code.splitlines()]
        
        # 写回文件
        new_content = "".join(lines)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        logger.info(f"已应用 {len(fixes)} 个修复到 {file_path}")
    
    async def run_full_workflow(
        self,
        path: Path,
        repo_name: Optional[str] = None,
        dry_run: bool = False,
        interactive: bool = False,
    ) -> Dict[str, Any]:
        """
        运行完整的工作流：扫描→分析→修复→PR→CI验证
        """
        # 1. 扫描和修复
        issues, fixes = await self.fix(path, dry_run=dry_run, interactive=interactive)
        
        result = {
            "files_scanned": 0,  # TODO: 统计
            "issues_found": len(issues),
            "fixes_applied": len(fixes),
            "pr_url": None,
            "ci_passed": None,
        }
        
        # 2. 如果有GitHub配置，创建PR
        if repo_name and self.github and not dry_run and fixes:
            try:
                pr_url = await self.github.create_pull_request(
                    repo_name=repo_name,
                    title="Auto-fix: 自动修复代码审计发现的问题",
                    fixes=fixes,
                )
                result["pr_url"] = pr_url
                
                # 3. 触发并等待CI
                if pr_url:
                    # 提取分支名
                    branch_name = f"auto-fix/code-audit-ai-agent-{hash(str(fixes))[:8]}"
                    ci_passed = await self.github.trigger_ci(repo_name, branch_name)
                    result["ci_passed"] = ci_passed
                    
            except Exception as e:
                logger.error(f"创建PR失败: {e}")
        
        return result
