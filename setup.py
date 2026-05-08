#!/usr/bin/env python3
"""
Setup script for Code Audit AI Agent
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README
readme = Path(__file__).parent / "README.md"
long_description = readme.read_text(encoding="utf-8")

# 读取requirements
requirements = Path(__file__).parent / "requirements.txt"
install_requires = []
if requirements.exists():
    with open(requirements, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("python"):
                install_requires.append(line)

setup(
    name="code-audit-ai-agent",
    version="0.1.0",
    description="自动化代码审计与优化的AI Agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/your-username/code-audit-ai-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Security",
    ],
    python_requires=">=3.9",
    install_requires=install_requires,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=24.0.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "code-audit=code_audit_ai_agent.__main__:main",
        ],
    },
    keywords="code-audit, ai, agent, code-review, security, optimization",
    license="MIT",
)
