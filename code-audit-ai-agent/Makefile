.PHONY: install test lint format clean

# 默认目标
all: install

# 安装依赖
install:
	pip install -e .[dev]

# 运行测试
test:
	pytest tests/ -v

# 运行lint检查
lint:
	flake8 code_audit_ai_agent/
	mypy code_audit_ai_agent/

# 自动格式化代码
format:
	black code_audit_ai_agent/ tests/ examples/

# 清理构建文件
clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 运行演示
demo:
	python examples/demo.py

# 扫描示例代码
scan-example:
	python -m code_audit_ai_agent scan examples/
