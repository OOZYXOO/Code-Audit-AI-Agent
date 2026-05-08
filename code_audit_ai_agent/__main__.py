#!/usr/bin/env python3
"""
Code Audit AI Agent - 命令行入口
"""

import asyncio
import argparse
import sys
from pathlib import Path

from . import CodeAuditor
from .utils.logger import setup_logger
from .utils.config import load_config

def main():
    """主命令行入口"""
    parser = argparse.ArgumentParser(
        description="Code Audit AI Agent - 自动化代码审计与优化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "command",
        choices=["scan", "audit", "fix", "run"],
        help="要执行的命令: scan(仅扫描), audit(扫描+分析), fix(自动修复), run(完整工作流)"
    )
    
    parser.add_argument(
        "path",
        help="要扫描的代码目录路径"
    )
    
    parser.add_argument(
        "--severity",
        choices=["info", "warning", "error", "critical"],
        default="warning",
        help="最低严重级别 (默认: warning)"
    )
    
    parser.add_argument(
        "--exclude",
        help="排除的目录/文件，逗号分隔 (默认: venv,__pycache__,*.pyc)"
    )
    
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=1000,
        help="最大文件大小(KB) (默认: 1000)"
    )
    
    parser.add_argument(
        "--parallel",
        type=int,
        default=8,
        help="并行扫描的文件数 (默认: 8)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行，不修改文件"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="交互式确认每个修复"
    )
    
    parser.add_argument(
        "--repo",
        help="GitHub仓库名 (owner/repo)，用于自动PR功能"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细日志输出"
    )
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logger(verbose=args.verbose)
    
    # 加载配置
    config = load_config()
    
    # 验证路径
    target_path = Path(args.path)
    if not target_path.exists():
        logger.error(f"路径不存在: {args.path}")
        sys.exit(1)
    
    try:
        # 运行异步主函数
        asyncio.run(run_command(args, config, target_path, logger))
    except KeyboardInterrupt:
        logger.info("操作已取消")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {str(e)}", exc_info=args.verbose)
        sys.exit(1)

async def run_command(args, config, target_path, logger):
    """执行指定的命令"""
    auditor = CodeAuditor(
        config=config,
        severity=args.severity,
        exclude_patterns=args.exclude.split(",") if args.exclude else None,
        max_file_size_kb=args.max_file_size,
        parallel=args.parallel,
    )
    
    if args.command == "scan":
        logger.info("开始代码扫描...")
        issues = await auditor.scan_only(target_path)
        report_issues(issues, logger)
        
    elif args.command == "audit":
        logger.info("开始代码审计与AI分析...")
        issues, analysis = await auditor.audit(target_path)
        report_issues(issues, logger)
        report_analysis(analysis, logger)
        
    elif args.command == "fix":
        logger.info("开始自动修复...")
        issues, fixes = await auditor.fix(
            target_path,
            dry_run=args.dry_run,
            interactive=args.interactive
        )
        report_issues(issues, logger)
        report_fixes(fixes, logger, args.dry_run)
        
    elif args.command == "run":
        logger.info("执行完整自动化工作流...")
        if not args.repo:
            logger.warning("未指定GitHub仓库，将只执行本地修复")
        
        result = await auditor.run_full_workflow(
            target_path,
            repo_name=args.repo,
            dry_run=args.dry_run,
            interactive=args.interactive
        )
        report_workflow_result(result, logger)

def report_issues(issues, logger):
    """报告发现的问题"""
    if not issues:
        logger.info("✅ 未发现任何问题！")
        return
    
    logger.info(f"\n🔍 发现 {len(issues)} 个问题:")
    
    # 按严重级别分组
    by_severity = {}
    for issue in issues:
        by_severity.setdefault(issue.severity, []).append(issue)
    
    for severity in ["critical", "error", "warning", "info"]:
        if severity not in by_severity:
            continue
        issues_list = by_severity[severity]
        logger.info(f"\n{severity.upper()} ({len(issues_list)}):")
        
        for issue in issues_list[:10]:  # 只显示前10个
            logger.info(f"  • {issue.file_path}:{issue.line_number} - {issue.title}")
        
        if len(issues_list) > 10:
            logger.info(f"  ... 还有 {len(issues_list) - 10} 个问题")

def report_analysis(analysis, logger):
    """报告AI分析结果"""
    if not analysis:
        return
    
    logger.info(f"\n🤖 AI分析摘要:")
    logger.info(f"  可自动修复: {analysis.get('fixable_count', 0)} 个问题")
    logger.info(f"  需要人工干预: {analysis.get('manual_count', 0)} 个问题")
    logger.info(f"  总体健康评分: {analysis.get('health_score', 0)}/100")

def report_fixes(fixes, logger, dry_run):
    """报告修复结果"""
    if not fixes:
        logger.info("✅ 没有需要修复的问题")
        return
    
    action = "已生成" if dry_run else "已应用"
    logger.info(f"\n🔧 {action} {len(fixes)} 个修复:")
    
    for fix in fixes[:10]:
        logger.info(f"  • {fix.file_path}: {fix.issue_title}")
    
    if len(fixes) > 10:
        logger.info(f"  ... 还有 {len(fixes) - 10} 个修复")

def report_workflow_result(result, logger):
    """报告完整工作流结果"""
    logger.info(f"\n🎉 工作流执行完成！")
    logger.info(f"  扫描文件: {result.get('files_scanned', 0)}")
    logger.info(f"  发现问题: {result.get('issues_found', 0)}")
    logger.info(f"  自动修复: {result.get('fixes_applied', 0)}")
    
    if result.get('pr_url'):
        logger.info(f"  PR已创建: {result['pr_url']}")
    
    if result.get('ci_passed') is not None:
        status = "✅ 通过" if result['ci_passed'] else "❌ 失败"
        logger.info(f"  CI测试: {status}")

if __name__ == "__main__":
    main()
