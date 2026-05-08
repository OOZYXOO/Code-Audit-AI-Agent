"""
扫描器测试
"""

import pytest
from pathlib import Path
from code_audit_ai_agent.scanner import CodeScanner, Severity, Issue

@pytest.mark.asyncio
async def test_scanner_basic():
    """测试基本扫描功能"""
    scanner = CodeScanner(
        severity_threshold=Severity.WARNING,
    )
    
    # 测试示例文件
    test_file = Path(__file__).parent.parent / "examples" / "example_bugs.py"
    assert test_file.exists()
    
    issues = await scanner.scan_file(test_file)
    
    # 应该能发现一些问题
    assert len(issues) > 0
    
    # 检查是否检测到了我们预期的问题
    issue_types = {issue.issue_type for issue in issues}
    
    # 应该检测到裸except
    assert "bare_except" in issue_types
    
    # 应该检测到硬编码密钥
    assert "hardcoded_secret" in issue_types
    
    # 应该检测到循环内字符串拼接
    assert "string_concat_loop" in issue_types

def test_issue_severity():
    """测试问题严重级别"""
    issue = Issue(
        issue_type="test",
        severity=Severity.WARNING,
        title="Test",
        description="Test",
        file_path=Path("test.py"),
        line_number=1,
    )
    
    assert issue.severity == Severity.WARNING
    assert issue.to_dict()["severity"] == "warning"

def test_should_exclude():
    """测试排除逻辑"""
    scanner = CodeScanner()
    
    # venv应该被排除
    assert scanner.should_exclude(Path("venv/bin/python")) is True
    
    # __pycache__应该被排除
    assert scanner.should_exclude(Path("__pycache__/test.cpython-39.pyc")) is True
    
    # 普通文件不应该被排除
    assert scanner.should_exclude(Path("src/main.py")) is False
