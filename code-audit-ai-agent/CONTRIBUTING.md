# 贡献指南

感谢你对 Code Audit AI Agent 项目的兴趣！我们欢迎各种形式的贡献。

## 如何贡献

### 报告 Bug

如果你发现了 bug，请通过 GitHub Issues 报告，包含：
- 问题的详细描述
- 复现步骤
- 预期行为和实际行为
- 你的环境信息（Python版本、操作系统等）

### 提交功能请求

我们欢迎新功能的建议！请通过 Issues 提交，说明：
- 你想要的功能
- 这个功能解决了什么问题
- 可能的实现方式

### 提交代码

1. Fork 这个仓库
2. 创建你的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交你的修改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

### 开发环境设置

```bash
# 克隆你的 fork
git clone https://github.com/your-username/code-audit-ai-agent.git
cd code-audit-ai-agent

# 安装开发依赖
make install
```

### 代码规范

- 我们使用 Black 进行代码格式化
- 使用 flake8 进行 lint 检查
- 使用 mypy 进行类型检查
- 确保所有测试通过

在提交 PR 之前，请运行：
```bash
make format  # 自动格式化
make lint    # 检查代码规范
make test    # 运行测试
```

### 添加新的扫描规则

如果你想添加新的问题检测规则：

1. 在对应的扫描器中添加检测逻辑：
   - 安全问题：`scanner/security.py`
   - 性能问题：`scanner/performance.py`
   - 规范问题：`scanner/style.py`

2. 添加测试用例来验证你的规则

3. 更新文档说明新的规则

### 添加新的 LLM 支持

如果你想支持新的大语言模型：

1. 在 `agent/` 目录下创建新的 Agent 类，继承自 `AIAgent`
2. 实现必要的接口方法
3. 在 `agent/__init__.py` 的 `create_agent` 工厂函数中添加支持
4. 更新配置文档

## MiMo 集成

我们正在积极开发 Xiaomi MiMo 模型的集成！如果你有兴趣参与这部分工作：

- 查看 `agent/mimo_agent.py`
- 帮助我们完善 MiMo API 的调用
- 测试长上下文能力
- 优化成本效益

## 行为准则

请保持友好、尊重的交流氛围。我们致力于打造一个开放、包容的社区。

## 问题？

如果你有任何问题，可以直接开一个 Issue，我们会尽快回复你！
