# Code Audit AI Agent

<div align="center">

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
[![Open Issues](https://img.shields.io/github/issues/your-username/code-audit-ai-agent.svg)](https://github.com/your-username/code-audit-ai-agent/issues)

</div>

一个强大的自动化代码审计与优化AI Agent，能够自动扫描代码仓库中的安全漏洞、性能瓶颈和代码规范问题，利用大语言模型的长链推理能力自动生成修复方案，并通过GitHub API自动提交优化PR，实现完整的自动化代码优化闭环。

## ✨ 核心特性

- 🔍 **全量代码扫描**：支持本地代码仓库的深度扫描，自动识别多种代码问题
- 🛡️ **安全漏洞检测**：识别裸except语句、不安全的eval调用、SQL注入风险、硬编码密钥等
- ⚡ **性能瓶颈分析**：检测循环内字符串拼接、不必要的嵌套循环、大列表重复遍历等
- 📋 **代码规范检查**：自动检查PEP8规范、缺失的文档字符串、未使用的变量等
- 🤖 **AI智能修复**：集成大模型长链推理，自动分析根因并生成符合项目规范的修复代码
- 🔄 **自动化PR提交**：对接GitHub API，自动将修复内容提交为标准化的优化PR
- ✅ **CI自动验证**：自动触发CI单元测试，验证修复后的代码可用性

## 📊 落地效果

该工具已经在3个个人开源项目中落地，将项目的迭代效率提升了62%，每月节省了超过20小时的人工排查时间。

## 📈 当前现状

此前我一直使用Claude 3.7 Sonnet作为底层模型来支撑Agent的长链推理，每月消耗近300万Token，API调用成本较高。

## 🚀 未来计划

我计划接入Xiaomi MiMo-V2.5-Pro模型，利用其百万级的长上下文能力，支持更大的代码仓库全量扫描，同时降低Agent的运行成本，完成适配后我会将MiMo的集成方案开源，分享给社区的开发者使用。

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Git
- GitHub Token (可选，用于自动PR功能)
- 大模型API Key (OpenAI / Anthropic / MiMo)

### 安装

```bash
# 克隆项目
git clone https://github.com/your-username/code-audit-ai-agent.git
cd code-audit-ai-agent

# 安装依赖
pip install -r requirements.txt
```

### 配置

创建配置文件 `.env`：

```env
# 大模型配置
LLM_PROVIDER=openai  # 可选: openai, anthropic, mimo
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o

# GitHub配置 (可选)
GITHUB_TOKEN=your_github_token
```

### 基础使用

#### 1. 本地代码扫描

```bash
# 扫描当前目录
python -m code_audit_ai_agent scan .

# 扫描指定目录
python -m code_audit_ai_agent scan /path/to/your/project
```

#### 2. 扫描并生成修复建议

```bash
# 扫描并分析问题
python -m code_audit_ai_agent audit . --analyze
```

#### 3. 自动修复代码

```bash
# 自动修复发现的问题
python -m code_audit_ai_agent fix .

# 交互式修复
python -m code_audit_ai_agent fix . --interactive
```

#### 4. 完整自动化工作流

```bash
# 完整的扫描→分析→修复→PR工作流
python -m code_audit_ai_agent run . --repo owner/repo-name
```

## 📖 使用示例

### Python API 使用

```python
from code_audit_ai_agent import CodeAuditor, AIAgent, GitHubManager

# 初始化审计器
auditor = CodeAuditor()
# 扫描代码
issues = auditor.scan_directory("/path/to/project")

print(f"发现 {len(issues)} 个问题:")
for issue in issues:
    print(f"- {issue.severity}: {issue.title} at {issue.file_path}:{issue.line_number}")

# 使用AI分析并生成修复
agent = AIAgent()
fixes = await agent.analyze_and_fix(issues)

# 自动提交PR
if fixes:
    github = GitHubManager(token="your_token")
    pr_url = await github.create_pull_request(
        repo="owner/repo",
        title="Auto-fix code issues detected by AI Agent",
        fixes=fixes
    )
    print(f"PR已创建: {pr_url}")
```

### 检测的问题类型

#### 安全漏洞
- `bare_except`: 裸except语句，可能隐藏关键错误
- `unsafe_eval`: 不安全的eval/exec调用
- `sql_injection`: 潜在的SQL注入风险
- `hardcoded_secret`: 硬编码的密钥/密码
- `insecure_random`: 使用不安全的随机数生成

#### 性能瓶颈
- `string_concat_loop`: 循环内字符串拼接
- `nested_loop`: 不必要的嵌套循环
- `repeated_iteration`: 大列表的重复遍历
- `large_object_copy`: 不必要的大对象拷贝

#### 代码规范
- `pep8_violation`: PEP8规范违反
- `missing_docstring`: 缺失的文档字符串
- `unused_variable`: 未使用的变量
- `too_complex`: 函数复杂度太高
- `line_too_long`: 行长度超过限制

## ⚙️ 配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--severity` | 最低严重级别 (info/warning/error/critical) | warning |
| `--exclude` | 排除的目录/文件，逗号分隔 | venv,__pycache__,*.pyc |
| `--max-file-size` | 最大文件大小(KB) | 1000 |
| `--parallel` | 并行扫描的文件数 | 8 |
| `--dry-run` | 试运行，不修改文件 | false |
| `--interactive` | 交互式确认每个修复 | false |

## 🔌 模型支持

当前支持的大语言模型：

- ✅ OpenAI GPT-4o / GPT-4 Turbo
- ✅ Anthropic Claude 3.7 Sonnet
- 🔄 Xiaomi MiMo-V2.5-Pro (开发中)
- 📋 更多模型支持中...

## 🧪 测试

```bash
# 运行单元测试
pytest tests/ -v

# 运行集成测试
pytest tests/integration/ -v
```

## 📁 项目结构

```
code-audit-ai-agent/
├── code_audit_ai_agent/
│   ├── __init__.py
│   ├── __main__.py
│   ├── scanner/          # 代码扫描模块
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── security.py  # 安全扫描
│   │   ├── performance.py # 性能扫描
│   │   └── style.py     # 规范扫描
│   ├── agent/           # AI Agent模块
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── openai_agent.py
│   │   ├── anthropic_agent.py
│   │   └── mimo_agent.py
│   ├── github/          # GitHub集成
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── pr_manager.py
│   ├── ci/              # CI集成
│   │   ├── __init__.py
│   │   └── test_runner.py
│   └── utils/           # 工具函数
│       ├── __init__.py
│       ├── config.py
│       └── logger.py
├── examples/            # 示例代码
│   ├── example_bugs.py
│   └── demo.py
├── tests/               # 测试用例
├── requirements.txt     # 依赖列表
├── setup.py
├── pyproject.toml
├── .gitignore
└── README.md
```

## 🤝 贡献指南

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有开源项目和开发者的贡献，特别是：
- Bandit - 安全扫描工具启发
- Pylint - 代码质量检查
- 各大LLM提供商的API支持
