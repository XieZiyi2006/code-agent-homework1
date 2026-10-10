"""Safe, inspectable tools available to the Code Agent."""

from __future__ import annotations

import ast
import fnmatch
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List


class ToolError(RuntimeError):
    """Expected tool failure that can be shown to the Agent/user."""


@dataclass
class ToolResult:
    name: str
    ok: bool
    data: Dict[str, Any]


class ToolRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self._tools: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}

    def register(self, name: str, function: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        self._tools[name] = function

    def names(self) -> List[str]:
        return sorted(self._tools)

    def run(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        if name not in self._tools:
            return ToolResult(name, False, {"error": f"未知工具: {name}"})
        try:
            return ToolResult(name, True, self._tools[name](arguments))
        except ToolError as exc:
            return ToolResult(name, False, {"error": str(exc)})
        except Exception as exc:  # defensive boundary around external tool code
            return ToolResult(name, False, {"error": f"工具内部异常: {type(exc).__name__}: {exc}"})

    def _path(self, value: str) -> Path:
        candidate = Path(value)
        resolved = (candidate if candidate.is_absolute() else self.root / candidate).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ToolError("拒绝访问项目根目录之外的路径") from exc
        return resolved


def build_default_registry(root: Path) -> ToolRegistry:
    registry = ToolRegistry(root)

    def read_file(args: Dict[str, Any]) -> Dict[str, Any]:
        path = registry._path(str(args.get("path", "")))
        if not path.is_file():
            raise ToolError(f"文件不存在: {path.relative_to(registry.root)}")
        max_chars = max(100, min(int(args.get("max_chars", 12000)), 30000))
        raw = path.read_bytes()
        text = None
        for encoding in ("utf-8", "utf-8-sig", "gb18030"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            raise ToolError("文件不是可识别的文本编码")
        return {"path": str(path.relative_to(registry.root)), "content": text[:max_chars], "truncated": len(text) > max_chars}

    def search_files(args: Dict[str, Any]) -> Dict[str, Any]:
        query = str(args.get("query", "")).strip()
        if not query:
            raise ToolError("搜索词不能为空")
        pattern = str(args.get("glob", "*.py"))
        limit = max(1, min(int(args.get("max_results", 20)), 100))
        ignored = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
        matches: List[Dict[str, Any]] = []
        for path in registry.root.rglob("*"):
            if len(matches) >= limit or not path.is_file() or any(part in ignored for part in path.parts):
                continue
            if not fnmatch.fnmatch(path.name, pattern):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for number, line in enumerate(text.splitlines(), 1):
                if query.lower() in line.lower():
                    matches.append({"path": str(path.relative_to(registry.root)), "line": number, "text": line.strip()})
                    if len(matches) >= limit:
                        break
        return {"query": query, "matches": matches, "count": len(matches)}

    def inspect_python(args: Dict[str, Any]) -> Dict[str, Any]:
        path = registry._path(str(args.get("path", "")))
        if not path.is_file() or path.suffix != ".py":
            raise ToolError("inspect_python 需要项目内的 .py 文件")
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            return {"path": str(path.relative_to(registry.root)), "syntax_error": f"第 {exc.lineno} 行: {exc.msg}", "classes": [], "functions": [], "issues": ["存在语法错误"]}
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        issues: List[str] = []
        todos: List[str] = []
        for number, line in enumerate(source.splitlines(), 1):
            if "TODO" in line or "FIXME" in line:
                todos.append(f"第 {number} 行: {line.strip()}")
        if todos:
            issues.append(f"发现 {len(todos)} 个 TODO/FIXME")
        if any(isinstance(node, ast.ExceptHandler) and node.type is None for node in ast.walk(tree)):
            issues.append("存在裸 except，可能掩盖异常")
        if "self.lower_layer.receive(" in source and "def send_down" in source:
            issues.append("send_down 直接调用 lower_layer.receive，可能跳过下层封装并提前解封装")
        if not issues:
            issues.append("未发现内置规则定义的明显问题")
        return {"path": str(path.relative_to(registry.root)), "syntax_error": None, "classes": classes, "functions": functions, "issues": issues, "todos": todos}

    def run_tests(args: Dict[str, Any]) -> Dict[str, Any]:
        target = registry._path(str(args.get("path", ".")))
        if not target.exists():
            raise ToolError(f"测试路径不存在: {target.relative_to(registry.root)}")
        if not target.is_dir():
            raise ToolError("run_tests 只接受项目内的测试目录，不直接执行任意 Python 文件")
        command = [sys.executable, "-m", "unittest", "discover", "-s", str(target)]
        try:
            completed = subprocess.run(command, cwd=registry.root, capture_output=True, text=True, timeout=15)
        except subprocess.TimeoutExpired as exc:
            raise ToolError("测试运行超时（15 秒）") from exc
        output = (completed.stdout + "\n" + completed.stderr).strip()
        return {"command": " ".join(command), "returncode": completed.returncode, "passed": completed.returncode == 0, "output": output[-6000:]}

    registry.register("read_file", read_file)
    registry.register("search_files", search_files)
    registry.register("inspect_python", inspect_python)
    registry.register("run_tests", run_tests)
    return registry

