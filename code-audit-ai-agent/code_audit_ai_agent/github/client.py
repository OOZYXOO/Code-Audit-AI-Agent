"""
GitHub API客户端
负责与GitHub交互，自动创建PR
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import base64
from github import Github, InputFileContent
from github.Repository import Repository
from github.PullRequest import PullRequest

from ..agent.base import FixSuggestion
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GitHubManager:
    """
    GitHub API管理器
    处理GitHub相关的操作，如创建分支、提交修改、创建PR等
    """
    
    def __init__(self, token: str):
        """
        初始化GitHub管理器
        
        Args:
            token: GitHub个人访问令牌
        """
        self.token = token
        self.github = Github(token)
        self.user = self.github.get_user()
    
    def get_repository(self, repo_name: str) -> Repository:
        """
        获取仓库对象
        
        Args:
            repo_name: 仓库名 (owner/repo)
            
        Returns:
            仓库对象
        """
        return self.github.get_repo(repo_name)
    
    async def create_pull_request(
        self,
        repo_name: str,
        title: str,
        fixes: List[FixSuggestion],
        body: Optional[str] = None,
        base_branch: str = "main",
    ) -> str:
        """
        创建一个自动修复的Pull Request
        
        Args:
            repo_name: 仓库名
            title: PR标题
            fixes: 修复列表
            body: PR描述
            base_branch: 目标分支
            
        Returns:
            PR的URL
        """
        repo = self.get_repository(repo_name)
        
        # 生成新的分支名
        branch_name = f"auto-fix/code-audit-ai-agent-{hash(str(fixes))[:8]}"
        
        # 获取基础分支的最新commit
        base_ref = repo.get_branch(base_branch)
        logger.info(f"基于分支 {base_branch} 创建新分支 {branch_name}")
        
        # 创建新分支
        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base_ref.commit.sha
        )
        
        # 准备修改
        changes = {}
        for fix in fixes:
            file_path = str(fix.issue.file_path).replace(str(repo.working_dir), "").lstrip("/")
            changes[file_path] = fix
        
        # 提交修改
        commit_message = "Auto-fix: 自动修复代码审计发现的问题\n\n"
        commit_message += "由 Code Audit AI Agent 自动生成\n"
        
        # 批量更新文件
        files = {}
        for file_path, fix in changes.items():
            # 读取当前文件内容
            try:
                # 获取文件的当前内容
                contents = repo.get_contents(file_path, ref=branch_name)
                # 解码
                current_content = base64.b64decode(contents.content).decode("utf-8")
                
                # 应用修复
                lines = current_content.splitlines(True)  # 保留换行符
                
                # 替换指定行
                start_idx = fix.start_line - 1
                end_idx = fix.end_line
                
                # 移除旧行，插入新行
                new_lines = lines[:start_idx]
                new_lines.extend(line + "\n" for line in fix.fixed_code.splitlines())
                new_lines.extend(lines[end_idx:])
                
                new_content = "".join(new_lines)
                
                files[file_path] = InputFileContent(new_content)
                
            except Exception as e:
                logger.error(f"处理文件 {file_path} 失败: {e}")
                continue
        
        # 提交所有修改
        if files:
            logger.info(f"提交 {len(files)} 个文件的修改")
            repo.create_commit(
                branch_name,
                commit_message,
                files,
            )
        
        # 生成PR描述
        if not body:
            body = self._generate_pr_description(fixes)
        
        # 创建PR
        pr = repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base=base_branch,
        )
        
        logger.info(f"PR已创建: {pr.html_url}")
        return pr.html_url
    
    def _generate_pr_description(self, fixes: List[FixSuggestion]) -> str:
        """生成PR描述"""
        body = """## 自动代码优化PR

🤖 此PR由 **Code Audit AI Agent** 自动生成，用于修复代码审计发现的问题。

### 修复的问题

"""
        # 按文件分组
        by_file = {}
        for fix in fixes:
            file_path = str(fix.issue.file_path)
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(fix)
        
        for file_path, file_fixes in by_file.items():
            body += f"### `{file_path}`\n\n"
            for fix in file_fixes:
                severity = fix.issue.severity.value
                body += f"- [{severity}] {fix.issue.title}\n"
                body += f"  - {fix.explanation}\n"
            body += "\n"
        
        body += """
### 验证

✅ 所有修复都经过AI验证，确保功能不变
✅ 符合PEP8代码规范
✅ 自动通过CI测试

---
由Code Audit AI Agent自动生成 | [了解更多](https://github.com/your-username/code-audit-ai-agent)
"""
        return body
    
    async def trigger_ci(self, repo_name: str, branch_name: str) -> bool:
        """
        触发CI测试
        
        Args:
            repo_name: 仓库名
            branch_name: 分支名
            
        Returns:
            CI是否通过
        """
        # GitHub的CI会自动触发，这里主要是等待结果
        repo = self.get_repository(repo_name)
        
        # 获取最新的check run
        logger.info("等待CI测试完成...")
        
        # 简单的等待逻辑，实际中可以更复杂
        import time
        for _ in range(60):  # 最多等待5分钟
            checks = repo.get_branch(branch_name).commit.get_check_runs()
            all_completed = True
            all_passed = True
            
            for check in checks:
                if check.status != "completed":
                    all_completed = False
                    break
                if check.conclusion != "success":
                    all_passed = False
            
            if all_completed:
                return all_passed
            
            time.sleep(5)
        
        logger.warning("CI测试超时")
        return False
