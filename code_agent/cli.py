"""Command-line interface for the Code Agent."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Optional

from .agent import Agent
from .providers import OpenAICompatibleProvider


def _default_model() -> str:
    configured_model = os.getenv("CODE_AGENT_MODEL")
    if configured_model:
        return configured_model
    if "api.deepseek.com" in os.getenv("CODE_AGENT_BASE_URL", "").lower():
        return "deepseek-chat"
    return "gpt-4o-mini"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Homework 1 Code Agent")
    parser.add_argument("--root", default=".", help="允许 Agent 读取的项目根目录")
    parser.add_argument("--query", help="单次查询；不提供时进入交互模式")
    parser.add_argument("--show-trace", action="store_true", help="显示 Agent 循环轨迹")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="强制启用 OpenAI-compatible LLM（保留用于兼容旧命令）",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="强制使用离线模式，即使已经设置 API Key",
    )
    parser.add_argument(
        "--model",
        default=_default_model(),
        help="LLM 模型名（默认读取环境变量，并识别 DeepSeek 地址）",
    )
    return parser


def _make_agent(args: argparse.Namespace) -> Agent:
    has_api_key = bool(os.getenv("CODE_AGENT_API_KEY"))
    use_llm = not args.offline and (args.llm or has_api_key)
    provider = OpenAICompatibleProvider(model=args.model) if use_llm else None
    return Agent(Path(args.root), provider=provider)


def _print_result(result, show_trace: bool) -> None:
    print(result.answer)
    if show_trace:
        print("\n--- trace ---")
        print("\n".join(result.trace))


def main(argv: Optional[List[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    agent = _make_agent(args)
    if args.query:
        _print_result(agent.run(args.query), args.show_trace)
        return
    print("Code Agent 已启动。输入 exit/quit 退出。")
    while True:
        try:
            request = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if request.lower() in {"exit", "quit"}:
            break
        _print_result(agent.run(request), args.show_trace)

