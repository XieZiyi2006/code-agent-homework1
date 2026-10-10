# Homework 1：Code Agent

这是一个不依赖第三方库即可运行的代码助手 Agent，选择“代码审查 + 代码解释”方向，配套的示例代码来自题目提供的 `homework1.docx`：分层协议栈（应用层、传输层、网络层）。

## 已实现的作业要求

- Agent 循环：用户输入 → 意图识别/计划 → 工具调用 → 结果汇总 → 输出。
- 工具集成：安全读取文件、递归搜索、Python AST 静态检查、运行测试。
- 交互方式：命令行单次查询或交互式会话。
- 上下文记忆：保留最近若干轮对话，并把历史摘要加入后续回答。
- 错误处理与重试：工具失败自动重试；路径越界、文件不存在、语法错误均转换为可读错误，不使 Agent 崩溃。
- LLM 扩展：可选 OpenAI-compatible Chat Completions API；没有 API Key 时自动使用离线规则推理，保证本地可演示。
- 文档：本 README 与 [DESIGN.md](DESIGN.md) 分别说明使用方法和架构设计。

## 目录

```text
code_agent_homework1/
├── code_agent/                 # Agent、记忆、规划器、工具和 CLI
├── sample/layer_stack.py       # 根据 homework1.docx 整理的示例代码
├── tests/                      # 标准库 unittest 测试
├── DESIGN.md
├── README.md
└── pyproject.toml
```

## 快速运行

在本目录执行：

```powershell
py -m code_agent --root . --query "请审查 sample/layer_stack.py" --show-trace
py -m code_agent --root . --query "解释 sample/layer_stack.py 中 send 和 receive 的调用流程"
```

不传 `--query` 会进入交互模式：输入 `exit` 或 `quit` 退出。

运行测试：

```powershell
py -m unittest discover -s tests -v
```

## 可选 LLM 模式

设置 API Key 后，程序会默认连接远程 API，不再需要每次传入 `--llm`。推荐在 PowerShell 中配置：

```powershell
$env:CODE_AGENT_API_KEY = "your-key"
$env:CODE_AGENT_BASE_URL = "https://api.deepseek.com"
$env:CODE_AGENT_MODEL = "deepseek-chat"
py -m code_agent --root . --query "请审查 sample/layer_stack.py" --show-trace
```

如需临时关闭远程模型，可增加 `--offline`。`--llm` 参数仍然保留，用于兼容旧命令。

默认离线模式适合课堂演示。若有 OpenAI-compatible 服务，可在 PowerShell 中设置：

```powershell
$env:CODE_AGENT_API_KEY = "your-key"
$env:CODE_AGENT_BASE_URL = "https://api.openai.com/v1"
py -m code_agent --root . --llm --model gpt-4o-mini --query "审查 sample/layer_stack.py"
```

程序只使用 Python 标准库；未设置 `CODE_AGENT_API_KEY` 时，`--llm` 会给出提示并回退到离线回答。

## 示例输出（摘要）

```text
输入：请审查 sample/layer_stack.py
计划：inspect_python(sample/layer_stack.py) → read_file(sample/layer_stack.py)
结论：未发现语法错误或内置规则定义的明显问题。
建议：为 send/receive 的逐层封装链路和异常传播补充单元测试。
```

